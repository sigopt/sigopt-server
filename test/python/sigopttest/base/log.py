# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging


class CapturingHandler(logging.StreamHandler):
  def __init__(self, log_records):
    super().__init__()
    self.log_records = log_records

  def emit(self, record):
    self.log_records.append(record)


class LogCapturer:
  def __init__(self, logger_name):
    self.logger_name = logger_name
    self._log_records = []
    logging.getLogger(self.logger_name).addHandler(CapturingHandler(self._log_records))

  @property
  def log_records(self):
    return self._log_records
