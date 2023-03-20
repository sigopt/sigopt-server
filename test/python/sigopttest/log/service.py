# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import uuid

import mock
import pytest

from zigopt.log.service import LoggingService

from sigopttest.base.log import LogCapturer


# pylint: disable=unbalanced-tuple-unpacking


class TestLoggingService(object):
  @pytest.fixture
  def services(self):
    return mock.Mock()

  @pytest.fixture
  def logging_service(self, services):
    return LoggingService(services)

  def test_log(self, logging_service):
    log_capturer = LogCapturer("sigopttest.log")
    logging_service.getLogger("sigopttest.log").warning("Test %s", "arg")
    (log_record,) = log_capturer.log_records
    assert log_record.getMessage() == "Test arg"

  def test_extra(self, logging_service):
    log_capturer = LogCapturer("sigopttest.log")
    logging_service.getLogger("sigopttest.log").warning(
      "Message",
      extra={
        "extra_1": 1,
        "extra_2": 2,
      },
    )
    (log_record,) = log_capturer.log_records
    assert log_record.extra_1 == 1
    assert log_record.extra_2 == 2

  def test_extra_none(self, logging_service):
    log_capturer = LogCapturer("sigopttest.log")
    logging_service.getLogger("sigopttest.log").warning("Message", extra=None)
    (log_record,) = log_capturer.log_records
    assert log_record.getMessage() == "Message"

  def test_exception(self, logging_service):
    exc_info = (Exception(), None, None)
    log_capturer = LogCapturer("sigopttest.log")
    logging_service.getLogger("sigopttest.log").warning("Message", exc_info=exc_info)
    (log_record,) = log_capturer.log_records
    assert log_record.exc_info == exc_info

  def test_stack_info(self, logging_service):
    log_capturer = LogCapturer("sigopttest.log")
    logging_service.getLogger("sigopttest.log").warning("Message", stack_info=True)
    (log_record,) = log_capturer.log_records
    assert log_record.stack_info.startswith("Stack (most recent call last):")

  def test_request_ids(self, logging_service):
    request_id = str(uuid.uuid1())
    trace_id = str(uuid.uuid1())

    request = mock.Mock()
    request.id = request_id
    request.trace_id = trace_id
    log_capturer = LogCapturer("sigopttest.log")
    logging_service.set_request(request)
    assert logging_service.request.id == request.id
    assert logging_service.request.trace_id == request.trace_id
    logging_service.getLogger("sigopttest.log").warning("Message 1")

    request = mock.Mock()
    logging_service.getLogger("sigopttest.log").warning("Message 2", extra={"request": request})

    (
      log_record_1,
      log_record_2,
    ) = log_capturer.log_records
    assert log_record_1.request_id == log_record_2.request_id == request_id
    assert log_record_1.trace_id == log_record_2.trace_id == trace_id
    assert hasattr(log_record_1, "request") is False
    assert hasattr(log_record_2, "request") is True
    assert log_record_2.request == request

  def test_with_request(self, logging_service):
    assert logging_service.request is None

    request_id = str(uuid.uuid1())
    trace_id = str(uuid.uuid1())

    request = mock.Mock()
    request.id = request_id
    request.trace_id = trace_id

    logger = logging_service.with_request(request)
    assert logger.request is not None
    assert logger.request.id == request_id
    assert logger.request.trace_id == trace_id
