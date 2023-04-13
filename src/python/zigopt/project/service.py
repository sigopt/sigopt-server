# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any

import sqlalchemy
from sqlalchemy import tuple_

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime
from zigopt.project.model import Project
from zigopt.services.base import Service


def create_example_project(client_id, name="Examples", reference_id="sigopt-examples"):
  return Project(
    name=name,
    reference_id=reference_id,
    client_id=client_id,
    created_by=None,
  )


class ProjectExistsException(Exception):
  def __init__(self, reference_id):
    self.reference_id = reference_id
    super().__init__(f"The project {self.reference_id} already exists")


class ProjectService(Service):
  @property
  def project_query(self):
    return self.services.database_service.query(Project)

  def find_by_client_and_ids_query(self, client_id, project_ids):
    return self.project_query.filter(Project.client_id == client_id).filter(Project.id.in_(project_ids))

  def find_by_client_and_id(self, client_id, project_id):
    if project_id is None:
      return None
    return self.services.database_service.one_or_none(
      self.find_by_client_and_ids_query(client_id=client_id, project_ids=[project_id]),
    )

  def find_by_client_and_ids(self, client_id, project_ids):
    if not project_ids:
      return []
    return self.services.database_service.all(
      self.find_by_client_and_ids_query(client_id=client_id, project_ids=project_ids),
    )

  def find_by_client_and_reference_id_query(self, client_id, reference_id):
    return self.project_query.filter(Project.client_id == client_id).filter(Project.reference_id == reference_id)

  def find_by_client_and_reference_id(self, client_id, reference_id):
    if reference_id is None:
      return None
    return self.services.database_service.one_or_none(
      self.find_by_client_and_reference_id_query(client_id=client_id, reference_id=reference_id),
    )

  def find_by_client_and_user_query(self, client_id, user_id):
    return self.project_query.filter(Project.client_id == client_id).filter(Project.created_by == user_id)

  def find_by_client_and_user(self, client_id, user_id):
    return self.services.database_service.all(
      self.find_by_client_and_user_query(client_id=client_id, user_id=user_id),
    )

  def find_by_client_id_query(self, client_id):
    return self.project_query.filter(Project.client_id == client_id)

  def find_by_client_id(self, client_id):
    return self.services.database_service.all(
      self.find_by_client_id_query(client_id=client_id),
    )

  def count_by_client_id(self, client_id):
    return self.services.database_service.count(
      self.find_by_client_id_query(client_id=client_id),
    )

  def insert(self, project):
    try:
      self.services.database_service.insert(project)
    except sqlalchemy.exc.IntegrityError as ie:
      self.services.database_service.rollback_session()
      if 'duplicate key value violates unique constraint "projects_client_id_reference_id_key"' in str(ie):
        raise ProjectExistsException(project.reference_id) from ie
      raise
    return project

  def update(self, client_id, reference_id, name=None, data=None, deleted=None):
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

  def projects_for_experiments(self, experiments):
    if not experiments:
      return {}
    project_client_pairs = distinct([(e.project_id, e.client_id) for e in experiments if e.project_id is not None])
    if not project_client_pairs:
      return {}
    projects = self.project_query.filter(tuple_(Project.id, Project.client_id).in_(project_client_pairs))
    project_map = {(p.id, p.client_id): p for p in projects}
    return {e.id: project_map.get((e.project_id, e.client_id)) for e in experiments}

  def mark_as_updated_by_experiment(self, experiment, project_id=None):
    timestamp = experiment.date_updated
    project_id = project_id or experiment.project_id
    self.services.database_service.update_one_or_none(
      self.project_query.filter(Project.id == project_id).filter(
        Project.date_updated < timestamp.replace(microsecond=0)
      ),
      {Project.date_updated: timestamp},
    )

  def create_example_for_client(self, client_id, **kwargs):
    project = create_example_project(client_id=client_id, **kwargs)
    self.insert(project)
    return project
