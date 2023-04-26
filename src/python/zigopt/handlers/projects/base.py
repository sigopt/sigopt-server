# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.clients.base import ClientHandler
from zigopt.net.errors import NotFoundError


class ProjectHandler(ClientHandler):
  allow_development = True

  def __init__(self, services, request, client_id, project_reference_id):
    super().__init__(services, request, client_id)

    self.project_reference_id = project_reference_id
    self.project = None

  def find_objects(self):
    return extend_dict(
      super().find_objects(),
      {
        "project": self._find_project(),
      },
    )

  def _find_project(self):
    project = self.services.project_service.find_by_client_and_reference_id(
      client_id=self.client_id,
      reference_id=self.project_reference_id,
    )
    if project is None:
      raise NotFoundError(f"No project {self.project_reference_id} in client {self.client_id}")
    return project

  def can_act_on_objects(self, requested_permission, objects):
    assert self.auth is not None

    project = objects["project"]
    client = objects["client"]
    return (
      super().can_act_on_objects(requested_permission, objects)
      and self.auth.can_act_on_project(self.services, requested_permission, project)
      and project.client_id == client.id
    )
