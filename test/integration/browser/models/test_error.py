# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json


class ErrorInTest(Exception):
  def __init__(self, message):
    super().__init__(message)
    self.message = message


class FindElementErrorInTest(ErrorInTest):
  def __init__(self, no_such_element_exception):
    msg_text = no_such_element_exception.msg
    try:
      error_message = json.loads(msg_text)["errorMessage"]
    except Exception:
      error_message = msg_text
    super().__init__(error_message)
