# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
from collections.abc import Mapping, Sequence

from sqlalchemy import func
from sqlalchemy.orm import Query

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.experiment.model import Experiment
from zigopt.pagination.lib import DefinedField, FieldApiType
from zigopt.services.base import Service
from zigopt.training_run.defined_fields import TrainingRunDefinedFieldsExtractor
from zigopt.training_run.field_types import FieldDetails
from zigopt.training_run.model import TrainingRun


_NO_ARG = object()


class TrainingRunService(Service):
  def insert_training_runs(self, training_runs: Sequence[TrainingRun]) -> None:
    self.services.database_service.insert_all(training_runs)

  def find_by_id(self, training_run_id: int) -> TrainingRun | None:
    return self.services.database_service.one_or_none(
      self.services.database_service.query(TrainingRun).filter(TrainingRun.id == training_run_id)
    )

  def find_by_ids(self, training_run_ids: Sequence[int]) -> Sequence[TrainingRun]:
    if len(training_run_ids) == 0:
      return []

    query = self.services.database_service.query(TrainingRun).filter(TrainingRun.id.in_(training_run_ids))
    return self.services.database_service.all(query)

  def count_by_project(self, client_id: int, project_id: int) -> int:
    return self.count_by_projects(client_id, [project_id]).get(project_id, 0)

  def count_by_projects(self, client_id, project_ids: Sequence[int]) -> Mapping[int, int]:
    return dict(
      self.services.database_service.all(
        self.services.database_service.query(TrainingRun.project_id, func.count(TrainingRun.id))
        .filter(TrainingRun.client_id == client_id)
        .filter(TrainingRun.project_id.in_(project_ids))
        .filter(TrainingRun.deleted.is_(False))
        .group_by(TrainingRun.project_id)
      )
    )

  def mark_as_updated(self, training_run: TrainingRun, timestamp: datetime.datetime | None = None) -> None:
    if timestamp is None:
      timestamp = current_datetime()
    self.services.database_service.update_one_or_none(
      self.services.database_service.query(TrainingRun)
      .filter(TrainingRun.id == training_run.id)
      .filter(TrainingRun.updated < timestamp.replace(microsecond=0)),
      {
        TrainingRun.updated: timestamp,
      },
    )

  def set_deleted(self, training_run_id: int, deleted: bool = True) -> None:
    tr = self.services.database_service.one_or_none(
      self.services.database_service.query(TrainingRun).filter(TrainingRun.id == training_run_id)
    )
    if not tr:
      return
    if exp := self.services.experiment_service.find_by_id(tr.experiment_id, include_deleted=True):
      if tr.suggestion_id:
        self.services.processed_suggestion_service.set_delete_by_ids(exp, [tr.suggestion_id], deleted=deleted)
      if tr.observation_id:
        self.services.observation_service.set_delete(exp, tr.observation_id, deleted=deleted)

    self.services.database_service.update_one_or_none(
      self.services.database_service.query(TrainingRun).filter(TrainingRun.id == training_run_id),
      {
        TrainingRun.deleted: deleted,
      },
    )

  def delete_runs_in_experiment(self, experiment: Experiment) -> None:
    self.services.database_service.update(
      self.services.database_service.query(TrainingRun).filter(TrainingRun.experiment_id == experiment.id),
      {TrainingRun.deleted: True},
    )
    self.services.processed_suggestion_service.delete_all_for_experiment(experiment)
    self.services.observation_service.delete_all_for_experiment(experiment)

  def assert_is_training_run_query(self, query: Query) -> Query:
    assert any(
      column.get("entity") is TrainingRun for column in query.column_descriptions
    ), "No entity for the query is Training Run. Cannot perform Training Run query operation on it."
    return query

  def _readable_name(self, field):
    # pylint: disable=too-many-return-statements
    if "." not in field.name:
      return field.name
    if readable_name := (
      {
        "logs.stdout.content": "Output Logs",
        "logs.stderr.content": "Error Logs",
        "source_code.hash": "Source Hash",
        "source_code.content": "Source Code",
        "model.type": "Model Type",
      }
    ).get(field.name):
      return readable_name

    name_parts = field.name.split(".")
    if list_get(name_parts, 0) == "datasets":
      dataset_name = name_parts[1]
      if list_get(name_parts, 2) == "type":
        return f"{dataset_name} Type"
      if list_get(name_parts, 2) == "version":
        return f"{dataset_name} Version"
    if list_get(name_parts, 0) in ("assignments", "metadata"):
      return name_parts[1]
    if list_get(name_parts, 0) == "values":
      value_name = name_parts[1]
      if name_parts[2] == "value_stddev":
        return f"{value_name} Std. Dev"
      return value_name
    return field.name

  def _insert_custom_fields(self, fields: list[DefinedField]) -> None:
    id_field = find(fields, lambda f: f.key == "id")
    assert id_field
    id_count = id_field.field_count
    fields.extend(
      [
        DefinedField(
          api_type=FieldApiType.string,
          field_count=id_count,
          key="state",
          name="State",
          sortable=True,
        ),
        DefinedField(
          api_type=FieldApiType.numeric,
          field_count=id_count,
          key="checkpoint_count",
          name="Checkpoint Count",
          sortable=False,
        ),
        DefinedField(
          api_type=FieldApiType.boolean,
          field_count=id_count,
          key="optimized_suggestion",
          name="Optimized Suggestion",
          sortable=True,
        ),
      ]
    )

  def _sanitize_defined_fields(self, fields: Sequence[DefinedField]) -> None:
    # TODO: Make this more generic
    for field in fields:
      name_parts = field.key.split(".")
      if list_get(name_parts, 0) == "values" and list_get(name_parts, 2) == "value_var":
        name_parts[2] = "value_stddev"
        field.key = ".".join(name_parts)
        field.name = ".".join(name_parts)

  def _insert_readable_names(self, fields: Sequence[DefinedField]) -> None:
    readable_names = distinct([self._readable_name(field) for field in fields])
    if len(readable_names) == len(fields):
      for field, readable_name in zip(fields, readable_names):
        field.name = readable_name

  def fetch_stored_fields(
    self,
    training_run_query: Query,
    fields_details: Sequence[FieldDetails] | None = None,
    by_organization: bool = False,
  ) -> list[DefinedField]:
    query = self.assert_is_training_run_query(training_run_query)
    return TrainingRunDefinedFieldsExtractor(
      self.services.database_service,
      query,
      fields_details=fields_details,
    ).extract_info(by_organization=by_organization)

  def get_defined_fields(self, training_run_query: Query, by_organization: bool = False) -> Sequence[DefinedField]:
    fields = self.fetch_stored_fields(training_run_query, by_organization=by_organization)
    self._insert_custom_fields(fields)
    self._sanitize_defined_fields(fields)
    self._insert_readable_names(fields)
    return fields
