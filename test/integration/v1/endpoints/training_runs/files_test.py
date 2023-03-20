# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import http

import pytest
import requests

from zigopt.project.model import Project
from zigopt.training_run.model import TrainingRun

from integration.base import RaisesApiException
from integration.v1.test_base import V1Base


class TestRunFiles(V1Base):
  @pytest.fixture
  def project(self, services, connection):
    project = Project(name="file test", client_id=connection.client_id, created_by=None, reference_id="file_test")
    services.database_service.insert(project)
    return project

  @pytest.fixture
  def training_run(self, services, project):
    training_run = TrainingRun(client_id=project.client_id, project_id=project.id)
    services.database_service.insert(training_run)
    return training_run

  @pytest.mark.parametrize(
    "content_length",
    [
      None,
      "1",
      -1,
      0,
      {},
      [],
      "",
    ],
  )
  def test_invalid_content_length(self, services, connection, training_run, content_length):
    b64_md5 = "CWVuO5yi2saakk6Jy1hHiQ=="
    name = "test run files invalid"
    filename = "test.txt"
    content_type = "text/plain"
    with RaisesApiException(http.HTTPStatus.BAD_REQUEST):
      (
        connection.training_runs(training_run.id)
        .files()
        .create(
          name=name,
          filename=filename,
          content_length=content_length,
          content_md5=b64_md5,
          content_type=content_type,
        )
      )

  @pytest.mark.parametrize(
    "content_md5",
    [
      None,
      "1",
      -1,
      0,
      {},
      [],
      "",
      "aGhlbGxv",
    ],
  )
  def test_invalid_content_md5(self, services, connection, training_run, content_md5):
    name = "test run files invalid"
    filename = "test.txt"
    content_type = "text/plain"
    with RaisesApiException(http.HTTPStatus.BAD_REQUEST):
      (
        connection.training_runs(training_run.id)
        .files()
        .create(
          name=name,
          filename=filename,
          content_length=1,
          content_md5=content_md5,
          content_type=content_type,
        )
      )

  @pytest.mark.parametrize(
    "content_type",
    [
      None,
      "1",
      -1,
      0,
      {},
      [],
      "hello/world",
      "image",
      "image/",
      "image/ ",
      "image/<>",
    ],
  )
  def test_invalid_content_type(self, services, connection, training_run, content_type):
    b64_md5 = "CWVuO5yi2saakk6Jy1hHiQ=="
    name = "test run files invalid"
    filename = "test.txt"
    with RaisesApiException(http.HTTPStatus.BAD_REQUEST):
      (
        connection.training_runs(training_run.id)
        .files()
        .create(
          name=name,
          filename=filename,
          content_length=1,
          content_md5=b64_md5,
          content_type=content_type,
        )
      )

  def test_create_and_download_file_for_run(self, services, connection, training_run):
    contents = "this\nis\na\ntest\n"
    b64_md5 = "CWVuO5yi2saakk6Jy1hHiQ=="
    name = "test run files"
    filename = "test.txt"
    content_type = "text/plain"
    file_info = (
      connection.training_runs(training_run.id)
      .files()
      .create(
        name=name,
        filename=filename,
        content_length=len(contents),
        content_md5=b64_md5,
        content_type=content_type,
      )
    )
    upload_info = file_info.upload
    response = requests.request(upload_info.method, upload_info.url, headers=upload_info.headers, data=contents)
    response.raise_for_status()
    updated_run = connection.training_runs(training_run.id).fetch()
    assert updated_run.files == [file_info.id]
    file_obj = connection.files(file_info.id).fetch()
    assert file_obj.name == name
    assert file_obj.filename == filename
    assert file_obj.content_length == len(contents)
    assert file_obj.content_md5 == b64_md5
    assert file_obj.content_type == content_type
    download_info = file_obj.download
    response = requests.get(download_info.url)
    response.raise_for_status()
    assert response.content.decode("utf-8") == contents

  def test_create_multiple_files(self, services, connection, training_run):
    contents_1 = "this\nis\na\ntest\n"
    b64_md5_1 = "CWVuO5yi2saakk6Jy1hHiQ=="
    contents_2 = "this\nis\nanother\ntest\n"
    b64_md5_2 = "hErGgMwOlw3IRZlwWueI+g=="
    file_1 = (
      connection.training_runs(training_run.id)
      .files()
      .create(
        name="test muliple files 1/2",
        filename="test.txt",
        content_length=len(contents_1),
        content_md5=b64_md5_1,
        content_type="text/plain",
      )
    )
    file_2 = (
      connection.training_runs(training_run.id)
      .files()
      .create(
        name="test muliple files 2/2",
        filename="test.txt",
        content_length=len(contents_2),
        content_md5=b64_md5_2,
        content_type="text/plain",
      )
    )
    updated_run = connection.training_runs(training_run.id).fetch()
    assert updated_run.files == [file_1.id, file_2.id]
