# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
class ResultOfTest(object):
  def __init__(self, success, message):
    self.success = success
    self.message = message
