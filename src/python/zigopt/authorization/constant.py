# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# Used to return a special status from a `can_act_on_X` check.
# Falsy so that this will lead to a denied authorization
class AuthorizationDenied:
  NEEDS_EMAIL_VERIFICATION: "AuthorizationDenied"

  def __init__(self, name: str):
    self.name = name

  def __bool__(self):
    return False


AuthorizationDenied.NEEDS_EMAIL_VERIFICATION = AuthorizationDenied("needs_email_verification")
