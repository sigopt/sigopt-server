# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest

from zigopt.project.model import Project
from zigopt.protobuf.gen.color.color_pb2 import Color
from zigopt.protobuf.gen.tag.tagdata_pb2 import TagData
from zigopt.tag.model import Tag
from zigopt.training_run.model import TrainingRun

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestRunTags(V1Base):
  @pytest.fixture
  def project(self, services, connection):
    project = Project(name="tag test", client_id=connection.client_id, created_by=None, reference_id="tag_test")
    services.database_service.insert(project)
    return project

  @pytest.fixture
  def training_run(self, services, project):
    training_run = TrainingRun(client_id=project.client_id, project_id=project.id)
    services.database_service.insert(training_run)
    return training_run

  @pytest.fixture
  def tags(self, services, connection):
    tags = []
    for i in range(2):
      tag = Tag(
        name=f"test run tags {i}",
        data=TagData(color=Color(red=1, green=2, blue=3)),
        client_id=connection.client_id,
      )
      services.database_service.insert(tag)
      tags.append(tag)
    return tags

  def test_add_tags_to_run(self, services, connection, training_run, tags):
    tag_map = {}
    for tag in tags:
      applied_tag = connection.training_runs(training_run.id).tags().create(id=tag.id)
      assert applied_tag.id == str(tag.id)
      assert applied_tag.color == "#010203"
      assert applied_tag.name == tag.name
      updated_run = services.database_service.one(
        services.database_service.query(TrainingRun).filter_by(id=training_run.id),
      )
      tag_map[tag.id] = True
      assert dict(updated_run.training_run_data.tags) == tag_map

  def test_add_tag_to_run_not_found(self, services, connection, training_run, tags):
    run_data = training_run.training_run_data
    for tag in tags:
      run_data.tags[tag.id] = True
    services.database_service.update_one(
      services.database_service.query(TrainingRun).filter_by(id=training_run.id),
      {TrainingRun.training_run_data: run_data},
    )

    with RaisesApiException(HTTPStatus.UNPROCESSABLE_ENTITY):
      connection.training_runs(training_run.id).tags().create(id=0)

    updated_run = services.database_service.one(
      services.database_service.query(TrainingRun).filter_by(id=training_run.id),
    )
    assert updated_run.training_run_data.tags == run_data.tags

  def test_remove_tags_from_run(self, services, connection, training_run, tags):
    tag_map = {tag.id: True for tag in tags}
    run_data = training_run.training_run_data
    for tag in tags:
      run_data.tags[tag.id] = True
    services.database_service.update_one(
      services.database_service.query(TrainingRun).filter_by(id=training_run.id),
      {TrainingRun.training_run_data: run_data},
    )
    updated_run = services.database_service.one(
      services.database_service.query(TrainingRun).filter_by(id=training_run.id),
    )
    for tag in tags:
      removed_tag = connection.training_runs(training_run.id).tags(tag.id).delete()
      assert removed_tag.id == str(tag.id)
      assert removed_tag.color == "#010203"
      assert removed_tag.name == tag.name
      updated_run = services.database_service.one(
        services.database_service.query(TrainingRun).filter_by(id=training_run.id),
      )
      del tag_map[tag.id]
      assert dict(updated_run.training_run_data.tags) == tag_map

  def test_remove_tag_from_run_not_found(self, services, connection, training_run, tags):
    run_data = training_run.training_run_data
    for tag in tags:
      run_data.tags[tag.id] = True
    services.database_service.update_one(
      services.database_service.query(TrainingRun).filter_by(id=training_run.id),
      {TrainingRun.training_run_data: run_data},
    )

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.training_runs(training_run.id).tags(0).delete()

    updated_run = services.database_service.one(
      services.database_service.query(TrainingRun).filter_by(id=training_run.id),
    )
    assert updated_run.training_run_data.tags == run_data.tags

  def test_run_detail_with_tags(self, services, connection, training_run, tags):
    def check_run_tags(expected_tags):
      fetched_run = connection.training_runs(training_run.id).fetch()
      assert set(str(t.id) for t in expected_tags) == set(fetched_run.tags)

    check_run_tags([])

    added_tags = []
    for tag in tags:
      connection.training_runs(training_run.id).tags().create(id=tag.id)
      added_tags.append(tag)
      check_run_tags(added_tags)

    leftover_tags = list(tags)
    for tag in tags:
      connection.training_runs(training_run.id).tags(tag.id).delete()
      leftover_tags.remove(tag)
      check_run_tags(leftover_tags)
