# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
def authentication_result(
  token=None,
  client=None,
  user=None,
  permission=None,
  membership=None,
  authenticated_from_email_link=None,
  authenticated_public_cert=None,
  authorization_response=None,
  session_expiration=None,
  organization=None,
):
  return {
    "token": token,
    "client": client,
    "user": user,
    "permission": permission,
    "membership": membership,
    "authenticated_from_email_link": authenticated_from_email_link,
    "authenticated_public_cert": authenticated_public_cert,
    "authorization_response": authorization_response,
    "session_expiration": session_expiration,
    "organization": organization,
  }
