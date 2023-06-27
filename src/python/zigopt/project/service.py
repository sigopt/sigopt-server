# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections.abc import Mapping, Sequence
from typing import Any

import sqlalchemy
from sqlalchemy import tuple_
from sqlalchemy.orm import Query

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.experiment.model import Experiment
from zigopt.project.model import Project
from zigopt.protobuf.gen.project.projectdata_pb2 import ProjectData
from zigopt.services.base import Service


def create_example_project(client_id: int, name: str = "Examples", reference_id: str = "sigopt-examples") -> Project:
  return Project(
    name=name,
    reference_id=reference_id,
    client_id=client_id,
    created_by=None,
  )


class ProjectExistsException(Exception):
  def __init__(self, reference_id: str):
    self.reference_id = reference_id
    super().__init__(f"The project {self.reference_id} already exists")


class ProjectService(Service):
  @property
  def project_query(self) -> Query:
    return self.services.database_service.query(Project)

  def find_by_client_and_ids_query(self, client_id: int, project_ids: Sequence[int]) -> Query:
    return self.project_query.filter(Project.client_id == client_id).filter(Project.id.in_(project_ids))

  def find_by_client_and_id(self, client_id: int, project_id: int) -> Project | None:
    if project_id is None:
      return None
    return self.services.database_service.one_or_none(
      self.find_by_client_and_ids_query(client_id=client_id, project_ids=[project_id]),
    )

  def find_by_client_and_ids(self, client_id: int, project_ids: Sequence[int]) -> Sequence[Project]:
    if not project_ids:
      return []
    return self.services.database_service.all(
      self.find_by_client_and_ids_query(client_id=client_id, project_ids=project_ids),
    )

  def find_by_client_and_reference_id_query(self, client_id: int, reference_id: str) -> Query:
    return self.project_query.filter(Project.client_id == client_id).filter(Project.reference_id == reference_id)

  def find_by_client_and_reference_id(self, client_id: int, reference_id: str) -> Project | None:
    if reference_id is None:
      return None
    return self.services.database_service.one_or_none(
      self.find_by_client_and_reference_id_query(client_id=client_id, reference_id=reference_id),
    )

  def find_by_client_and_user_query(self, client_id: int, user_id: int) -> Query:
    return self.project_query.filter(Project.client_id == client_id).filter(Project.created_by == user_id)

  def find_by_client_and_user(self, client_id: int, user_id: int) -> Sequence[Project]:
    return self.services.database_service.all(
      self.find_by_client_and_user_query(client_id=client_id, user_id=user_id),
    )

  def find_by_client_id_query(self, client_id: int) -> Query:
    return self.project_query.filter(Project.client_id == client_id)

  def find_by_client_id(self, client_id: int) -> Sequence[Project]:
    return self.services.database_service.all(
      self.find_by_client_id_query(client_id=client_id),
    )

  def count_by_client_id(self, client_id: int) -> int:
    return self.services.database_service.count(
      self.find_by_client_id_query(client_id=client_id),
    )

  def insert(self, project: Project) -> Project:
    try:
      self.services.database_service.insert(project)
    except sqlalchemy.exc.IntegrityError as ie:
      self.services.database_service.rollback_session()
      if 'duplicate key value violates unique constraint "projects_client_id_reference_id_key"' in str(ie):
        raise ProjectExistsException(project.reference_id) from ie
      raise
    return project

  def update(
    self,
    client_id: int,
    reference_id: str,
    name: str | None = None,
    data: ProjectData | None = None,
    deleted: bool | None = None,
  ) -> int:
    updates: dict[Any, Any | None] = {
      Project.name: name,
      Project.data: data,
      Project.date_updated: current_datetime(),
      Project.deleted: deleted,
    }
    return self.services.database_service.update_one(
      self.project_query.filter(Project.client_id == client_id).filter(Project.reference_id == reference_id),
      remove_nones_mapping(updates),
    )

  def projects_for_experiments(self, experiments: Sequence[Experiment]) -> Mapping[tuple[int, int], Project | None]:
    if not experiments:
      return {}
    project_client_pairs = distinct([(e.project_id, e.client_id) for e in experiments if e.project_id is not None])
    if not project_client_pairs:
      return {}
    projects = self.project_query.filter(tuple_(Project.id, Project.client_id).in_(project_client_pairs))
    project_map = {(p.id, p.client_id): p for p in projects}
    return {e.id: project_map.get((e.project_id, e.client_id)) for e in experiments}

  def mark_as_updated_by_experiment(self, experiment: Experiment, project_id: int | None = None) -> None:
    timestamp = experiment.date_updated
    project_id = project_id or experiment.project_id
    self.services.database_service.update_one_or_none(
      self.project_query.filter(Project.id == project_id).filter(
        Project.date_updated < timestamp.replace(microsecond=0)
      ),
      {Project.date_updated: timestamp},
    )

  def create_example_for_client(self, client_id: int, **kwargs) -> Project:
    project = create_example_project(client_id=client_id, **kwargs)
    self.insert(project)
    return project
