# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import logging
import os
import uuid

import pytest
from freezegun import freeze_time
from mock import Mock

from zigopt.common import remove_nones
from zigopt.log.base import JsonFormatter, SyslogFormatter


class TestJsonFormatter:
  @pytest.fixture
  @freeze_time("1989-08-12", tz_offset=0)
  def record(self):
    return logging.LogRecord(
      name="sigopt.log",
      level=30,
      pathname="/path",
      lineno=12,
      msg="Logging Message %s",
      args=("arg1",),
      exc_info=None,
    )

  def test_format(self, record):
    assert json.loads(JsonFormatter().format(record)) == {
      "clientId": None,
      "environment": "unknown",
      "level": "WARNING",
      "loggerName": "sigopt.log",
      "message": "Logging Message arg1",
      "pid": os.getpid(),
      "queryTime": None,
      "requestId": None,
      "status": None,
      "time": "1989-08-12 00:00:00,000",
      "traceId": None,
      "userId": None,
    }

  def test_legible(self, record):
    serialized = JsonFormatter().format(record)
    parsed = json.loads(serialized)
    assert "loggerName" in parsed
    assert "message" in parsed

  def test_request_ids(self):
    record = Mock()
    record.args = ()
    record.client_id = None
    record.created = 0
    record.exc_info = None
    record.exc_text = None
    record.getMessage.return_value = "unused"
    record.levelname = "unused"
    record.msecs = 0
    record.msg = "unused"
    record.name = "unused"
    record.process = 100
    record.query_time = None
    record.request = None
    record.stack_info = None
    record.status = None
    record.time = None
    record.trace_id = None
    record.user_id = None

    request_id = str(uuid.uuid1())
    trace_id = str(uuid.uuid1())
    record.request_id = request_id
    record.trace_id = trace_id

    record_json = json.loads(JsonFormatter().format(record))
    assert record_json["requestId"] == request_id
    assert record_json["traceId"] == trace_id


class TestSyslogFormatter:
  @pytest.fixture
  @freeze_time("1989-08-12", tz_offset=0)
  def record(self):
    return logging.LogRecord(
      name="sigopt.log",
      level=30,
      pathname="/path",
      lineno=12,
      msg="Logging Message %s",
      args=("arg1",),
      exc_info=None,
    )

  @freeze_time("1989-08-12", tz_offset=0)
  @pytest.fixture
  def mock_record(self):
    record = Mock()
    record.args = ()
    record.client_id = "unused"
    record.created = 0
    record.funcName = "function_name"
    record.getMessage.return_value = "unused"
    record.levelname = "unused"
    record.levelno = 30
    record.lineno = 12
    record.msecs = 0
    record.msg = "unused"
    record.name = "unused"
    record.pathname = "/path"
    record.process = 100
    record.query_time = "unused"
    record.request.id = "unused"
    record.request.method = "unused"
    record.request.path = "unused"
    record.request.sanitized_headers.return_value = {}
    record.request.sanitized_params.return_value = {}
    record.request.trace_id = "unused"
    record.request_id = "unused"
    record.status = "unused"
    record.trace_id = "unused"
    record.user_id = None
    return record

  def as_json(self, formatted):
    prefix = "Python: "
    assert formatted.startswith(prefix)
    return json.loads(formatted[len(prefix) :])

  @freeze_time("2018-01-01", tz_offset=0)
  def test_format(self, record):
    assert remove_nones(self.as_json(SyslogFormatter().format(record))) == {
      "environment": "unknown",
      "level": "WARNING",
      "loggerName": "sigopt.log",
      "message": "Logging Message arg1",
      "pid": os.getpid(),
      "time": "1989-08-12 00:00:00,000",
    }

  def test_query_time(self, mock_record):
    mock_record.query_time = 52
    assert self.as_json(SyslogFormatter().format(mock_record))["queryTime"] == 52

  def test_status(self, mock_record):
    mock_record.status = 404
    assert self.as_json(SyslogFormatter().format(mock_record))["status"] == 404

  def test_json_message(self, mock_record):
    mock_record.getMessage.return_value = '{"key":"value"}'
    assert self.as_json(SyslogFormatter().format(mock_record))["message"] == '{"key":"value"}'

  def test_request_ids(self, mock_record):
    request_id = str(uuid.uuid1())
    trace_id = str(uuid.uuid1())
    mock_record.request_id = request_id
    mock_record.trace_id = trace_id
    mock_record.request = None
    mock_record_json = self.as_json(SyslogFormatter().format(mock_record))
    assert mock_record_json["requestId"] == request_id
    assert mock_record_json["traceId"] == trace_id

  def test_request(self, mock_record):
    request_id = str(uuid.uuid1())
    trace_id = str(uuid.uuid1())
    mock_record.request.id = request_id
    mock_record.request.trace_id = trace_id
    mock_record.request.method = "GET"
    mock_record.request.path = "/v1/experiments"
    mock_record.request.sanitized_params.return_value = {"password": "***"}
    log = self.as_json(SyslogFormatter().format(mock_record))
    assert log["requestId"] == request_id
    assert log["traceId"] == trace_id
    assert log["requestMethod"] == "GET"
    assert log["requestURI"] == "/v1/experiments"
    assert log["requestParamsStr"] == '{"password": "***"}'

  def test_params_invalid_json(self, mock_record):
    mock_record.request.sanitized_params.side_effect = ValueError("Invalid JSON")
    log = self.as_json(SyslogFormatter().format(mock_record))
    assert log.get("requestParamsStr") is None
    assert log["requestParamsInvalidJSON"] is True
