# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common.strings import random_string
from zigopt.project.model import Project
from zigopt.protobuf.dict import dict_to_protobuf_struct

from integration.service.project.test_base import ProjectServiceTestBase


class TestProjectServiceUpdate(ProjectServiceTestBase):
  def find_project(self, services, client_id, reference_id):
    return services.database_service.one(
      services.database_service.query(Project)
      .filter(Project.client_id == client_id)
      .filter(Project.reference_id == reference_id)
    )

  def test_update_project_name(self, services, project_service, project):
    new_name = random_string()
    project_service.update(
      client_id=project.client_id,
      reference_id=project.reference_id,
      name=new_name,
    )
    updated_project = self.find_project(services, project.client_id, project.reference_id)
    assert updated_project.client_id == project.client_id
    assert updated_project.id == project.id
    assert updated_project.name == new_name
    assert updated_project.data == Project.data.default_value()
    assert updated_project.date_updated > project.date_updated

  def test_update_project_data(self, services, project_service, project):
    project_data = Project.data.default_value()
    project_data.metadata.CopyFrom((dict_to_protobuf_struct({"testing": random_string()})))
    project_service.update(
      client_id=project.client_id,
      reference_id=project.reference_id,
      data=project_data,
    )
    updated_project = self.find_project(services, project.client_id, project.reference_id)
    assert updated_project.client_id == project.client_id
    assert updated_project.id == project.id
    assert updated_project.name == project.name
    assert updated_project.data == project_data
    assert updated_project.date_updated > project.date_updated

  def test_update_project_all(self, services, project_service, project):
    new_name = random_string()
    project_data = Project.data.default_value()
    project_data.metadata.CopyFrom((dict_to_protobuf_struct({"testing": random_string()})))
    project_service.update(
      client_id=project.client_id,
      reference_id=project.reference_id,
      name=new_name,
      data=project_data,
    )
    updated_project = self.find_project(services, project.client_id, project.reference_id)
    assert updated_project.client_id == project.client_id
    assert updated_project.id == project.id
    assert updated_project.name == new_name
    assert updated_project.data == project_data
    assert updated_project.date_updated > project.date_updated
