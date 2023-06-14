# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
from typing import Any, Sequence

from sqlalchemy import Column, func
from sqlalchemy.orm import Query

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.conditionals.util import check_all_conditional_values_satisfied
from zigopt.db.column import JsonPath, jsonb_array_length, jsonb_set, jsonb_strip_nulls, unwind_json_path
from zigopt.experiment.constraints import InfeasibleConstraintsError, has_feasible_constraints
from zigopt.experiment.model import Experiment, ExperimentMetaProxy
from zigopt.math.domain_bounds import get_parameter_domain_bounds
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.api.paging_pb2 import PagingMarker
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentMeta, MetricImportance, MetricImportanceMap
from zigopt.protobuf.lib import copy_protobuf
from zigopt.services.base import Service

from libsigopt.aux.errors import SigoptValidationError
from libsigopt.aux.samplers import generate_uniform_random_points_rejection_sampling


NUM_SAMPLES_FOR_FLAG = 10
NUM_REJECTION_TRIALS_FOR_FLAG = 10000

TimeInterval = tuple[datetime.datetime, datetime.datetime]


class ExperimentService(Service):
  def _query_all(self) -> Query:
    return self.services.database_service.query(Experiment).filter(Experiment.deleted.isnot(True))

  def find_all(
    self, limit: int | None = None, before: PagingMarker | None = None, after: PagingMarker | None = None
  ) -> Sequence[Experiment]:
    q = self._query_all()
    return self.services.query_pager.get_page_results(q, Experiment.id, limit=limit, before=before, after=after)

  def count_all(
    self, limit: int | None = None, before: PagingMarker | None = None, after: PagingMarker | None = None
  ) -> int:
    q = self._query_all()
    return self.services.database_service.count(q)

  def find_by_id(self, experiment_id: int, include_deleted: bool = False) -> Experiment | None:
    return self.services.database_service.one_or_none(
      self._include_deleted_clause(
        include_deleted, self.services.database_service.query(Experiment).filter(Experiment.id == experiment_id)
      )
    )

  def _query_by_organization_id_for_billing(
    self, organization_id: int, time_interval: TimeInterval | None, lenient: bool
  ) -> Query:
    # NOTE: Intentionally includes deleted experiments and deleted observations
    # TODO(SN-1080): Doesn't handle deleted parameters... but that means if the users have deleted
    # parameters they get a little bit of a bonus so they are unlikely to complain
    observation_count = func.count(Observation.id).label("observation_count")
    query = (
      self.services.database_service.query(Experiment.id)
      .join(Client, Experiment.client_id == Client.id)
      .filter(Client.organization_id == organization_id)
      .filter(~Experiment.experiment_meta.development)
    )
    if lenient:
      query = (
        query.outerjoin(Observation, Experiment.id == Observation.experiment_id)
        .group_by(Experiment.id)
        .having(jsonb_array_length(Experiment.experiment_meta.all_parameters_unsorted) < observation_count)
      )
    if time_interval is not None:
      start, end = time_interval
      # NOTE: We hope to speed this query up by additionally filtering by date_updated.
      # We hope it is faster since date_updated is indexed.
      # We also know that date_created <= date_updated
      # Thus we know that date_created >= start implies date_updated >= start.
      # We cannot do this in the other direction, since date_created < end does not imply date_updated < end
      query = (
        query.filter(Experiment.date_created >= start)
        .filter(Experiment.date_updated >= start)
        .filter(Experiment.date_created < end)
      )
    return query

  def count_by_project(self, client_id: int, project_id: int) -> int:
    return self.count_by_projects(client_id, [project_id]).get(project_id, 0)

  def count_by_projects(self, client_id: int, project_ids: Sequence[int]) -> dict[int, int]:
    return dict(
      self.services.database_service.all(
        self.services.database_service.query(Experiment.project_id, func.count(Experiment.id))
        .filter(Experiment.client_id == client_id)
        .filter(Experiment.project_id.in_(project_ids))
        .group_by(Experiment.project_id)
      )
    )

  def _get_cached_count_by_organization_id_for_billing(
    self, organization_id: int, start_time: datetime.datetime | None
  ) -> int | None:
    experiment_cache_count_key = self.services.redis_key_service.create_experiment_count_by_org_billing_key(
      organization_id,
      start_time,
    )
    count = None
    with self.services.exception_logger.tolerate_exceptions(Exception):
      count = self.services.redis_service.get(experiment_cache_count_key)
    return napply(count, int)

  def _set_cached_count_by_organization_id_for_billing(
    self, organization_id: int, time_interval: TimeInterval | None, count: int
  ) -> None:
    start, end = time_interval or (None, None)
    experiment_cache_count_key = self.services.redis_key_service.create_experiment_count_by_org_billing_key(
      organization_id,
      start,
    )
    expire_at = None
    if end:
      end_buffer = datetime.timedelta(days=1)
      expire_at = end + end_buffer

    with self.services.exception_logger.tolerate_exceptions(Exception):
      self.services.redis_service.set(experiment_cache_count_key, count)
      if expire_at is not None:
        self.services.redis_service.set_expire_at(experiment_cache_count_key, expire_at)

  def incr_count_by_organization_id_for_billing(
    self, experiment: Experiment, organization_id: int, time_interval: TimeInterval | None = None
  ) -> None:
    if experiment.development:
      return
    redis_key = self.services.redis_key_service.create_experiment_count_by_org_billing_key(
      organization_id,
      time_interval and time_interval[0],
    )
    with self.services.exception_logger.tolerate_exceptions(Exception):
      if self.services.redis_service.exists(redis_key):
        self.services.redis_service.increment(redis_key)
      else:
        self.services.experiment_service.count_by_organization_id_for_billing(
          organization_id,
          time_interval,
          lenient=False,
          use_cache=False,
        )

  def count_by_organization_id_for_billing(
    self,
    organization_id: int,
    time_interval: TimeInterval | None,
    lenient=False,
    use_cache=False,
  ) -> int:
    if use_cache and lenient:
      self.services.exception_logger.soft_exception("cannot count_by_org for billing with both lenient and use_cache")
      use_cache = False
    if use_cache:
      start = time_interval and time_interval[0]
      count = self._get_cached_count_by_organization_id_for_billing(organization_id, start)
      if count is not None:
        return count
    q = self._query_by_organization_id_for_billing(
      organization_id,
      time_interval,
      lenient=lenient,
    )
    count = self.services.database_service.count(q) if q else 0
    self._set_cached_count_by_organization_id_for_billing(organization_id, time_interval, count)
    return count

  def insert(self, experiment: Experiment) -> Experiment:
    return_val = self.services.database_service.insert(experiment)
    if experiment.project_id is not None:
      self.services.project_service.mark_as_updated_by_experiment(
        experiment=experiment,
        project_id=experiment.project_id,
      )
    return return_val

  def force_hitandrun_sampling(self, experiment: Experiment, force: bool) -> Experiment:
    ret = self.update_meta(
      experiment.id,
      {Experiment.experiment_meta.force_hitandrun_sampling: force},
    )
    assert ret is not None
    meta: ExperimentMeta = copy_protobuf(experiment.experiment_meta)
    meta.force_hitandrun_sampling = force
    experiment.experiment_meta = ExperimentMetaProxy(meta)
    return ret

  # NOTE - if we implement the possibility for users to update metric names, we need to update the
  # importances when the names have changed (as they are currently keyed by metric names)
  def update_importance_maps(self, experiment: Experiment, importance_maps: dict[str, dict[str, float]]) -> Experiment:
    imap = {}
    for metric_name in importance_maps.keys():
      imap[metric_name] = MetricImportanceMap(
        importances={key: MetricImportance(importance=value) for key, value in importance_maps[metric_name].items()}
      )

    ret = self.update_meta(
      experiment.id,
      {
        Experiment.experiment_meta.importance_maps: imap,
      },
    )
    assert ret
    return ret

  def update_meta(self, experiment_id: int, params: dict[Column, Any]) -> Experiment | None:
    meta_clause = Experiment.experiment_meta
    for attribute, value in params.items():
      json_path = unwind_json_path(attribute)
      meta_clause = jsonb_set(meta_clause, JsonPath(*json_path), value)
    meta_clause = jsonb_strip_nulls(meta_clause)
    return self.services.database_service.update_one_or_none(
      self.services.database_service.query(Experiment).filter_by(id=experiment_id),
      {
        Experiment.experiment_meta: meta_clause,
      },
    )

  def delete(self, experiment: Experiment) -> None:
    """
        Not a true DB delete, just sets the deleted flag.
        """
    timestamp = current_datetime()
    update = self.services.database_service.update_one_or_none(
      self.services.database_service.query(Experiment).filter(Experiment.id == experiment.id),
      {
        Experiment.deleted: True,
        Experiment.date_updated: timestamp,
      },
    )
    if update:
      experiment.date_updated = timestamp
      experiment.deleted = True
      self.services.project_service.mark_as_updated_by_experiment(experiment)

  def delete_by_client_ids(self, client_ids: Sequence[int]) -> None:
    """
        Not a true DB delete, just sets the deleted flag.
        """
    self.services.database_service.update(
      self.services.database_service.query(Experiment)
      .filter(Experiment.client_id.in_(client_ids))
      .filter(Experiment.deleted.isnot(True)),
      {
        Experiment.deleted: True,
        Experiment.date_updated: current_datetime(),
      },
    )

  # More can probably be pushed in here depending on how modular we want services to be
  # Maybe consider using organization id instead of client id?
  def find_by_client_id(self, client_id: int) -> Sequence[Experiment]:
    return self.services.database_service.all(
      self.services.database_service.query(Experiment)
      .filter(Experiment.client_id == client_id)
      .filter(Experiment.deleted.isnot(True))
    )

  def _include_deleted_clause(self, include_deleted: bool, q: Query) -> Query:
    if not include_deleted:
      return q.filter(Experiment.deleted.isnot(True))
    return q

  def mark_as_updated(self, experiment: Experiment, timestamp: datetime.datetime | None = None) -> None:
    if timestamp is None:
      timestamp = current_datetime()
    did_update = self.services.database_service.update_one_or_none(
      self.services.database_service.query(Experiment)
      .filter(Experiment.id == experiment.id)
      .filter(Experiment.date_updated < timestamp.replace(microsecond=0)),
      {
        Experiment.date_updated: timestamp,
      },
    )
    if did_update:
      experiment.date_updated = timestamp
      self.services.project_service.mark_as_updated_by_experiment(experiment=experiment)

  def verify_experiment_acceptability(self, auth, experiment: Experiment, client: Client) -> None:
    try:
      has_feasible_constraints(experiment)
    except InfeasibleConstraintsError as e:
      raise SigoptValidationError(e) from e

    if experiment.experiment_meta.conditionals:
      check_all_conditional_values_satisfied(experiment.experiment_meta)

  def set_hitandrun_flag_using_rejection_sampling(self, experiment: Experiment) -> None:
    domain_bounds = get_parameter_domain_bounds(experiment.constrained_parameters)
    halfspaces = experiment.halfspaces
    A = halfspaces[:, :-1]
    b = -halfspaces[:, -1]
    _, rejection_succeeded = generate_uniform_random_points_rejection_sampling(
      NUM_SAMPLES_FOR_FLAG,
      domain_bounds,
      A,
      b,
      rejection_count=NUM_REJECTION_TRIALS_FOR_FLAG,
    )
    self.force_hitandrun_sampling(experiment, not rejection_succeeded)
