# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
class WorkerException(Exception):
  pass


class WorkerFinishedException(WorkerException):
  pass


class WorkerInterruptedException(WorkerException):
  pass


class WorkerKilledException(WorkerInterruptedException):
  pass
