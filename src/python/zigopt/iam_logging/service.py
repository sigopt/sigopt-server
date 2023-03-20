# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import uuid

from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.services.base import Service


class IamEvent(object):
  ORGANIZATION_CREATE = "OrganizationCreate"
  ORGANIZATION_DELETE = "OrganizationDelete"
  ORGANIZATION_UPDATE = "OrganizationUpdate"

  CLIENT_CREATE = "ClientCreate"
  CLIENT_DELETE = "ClientDelete"
  CLIENT_UPDATE = "ClientUpdate"

  USER_CREATE = "UserCreate"
  USER_DELETE = "UserDelete"
  USER_UPDATE = "UserUpdate"

  MEMBERSHIP_CREATE = "MembershipCreate"
  MEMBERSHIP_DELETE = "MembershipDelete"
  MEMBERSHIP_UPDATE = "MembershipUpdate"

  PERMISSION_CREATE = "PermissionCreate"
  PERMISSION_DELETE = "PermissionDelete"
  PERMISSION_UPDATE = "PermissionUpdate"

  USER_LOG_IN = "UserLogIn"
  USER_LOG_IN_RATE_LIMIT = "UserLogInRateLimit"

  ORGANIZATION_ADMIN_ROOT_LOG_IN = "OrganizationAdminRootLogIn"

  USER_LOG_OUT = "UserLogOut"  # web logout


ALL_IAM_EVENTS = {
  IamEvent.ORGANIZATION_CREATE,
  IamEvent.ORGANIZATION_UPDATE,
  IamEvent.ORGANIZATION_DELETE,
  IamEvent.CLIENT_CREATE,
  IamEvent.CLIENT_UPDATE,
  IamEvent.CLIENT_DELETE,
  IamEvent.USER_CREATE,
  IamEvent.USER_UPDATE,
  IamEvent.USER_DELETE,
  IamEvent.MEMBERSHIP_CREATE,
  IamEvent.MEMBERSHIP_UPDATE,
  IamEvent.MEMBERSHIP_DELETE,
  IamEvent.PERMISSION_CREATE,
  IamEvent.PERMISSION_UPDATE,
  IamEvent.PERMISSION_DELETE,
  IamEvent.USER_LOG_IN,
  IamEvent.USER_LOG_OUT,
  IamEvent.USER_LOG_IN_RATE_LIMIT,
}

_NO_REQUESTOR_EVENTS = {
  IamEvent.USER_LOG_IN_RATE_LIMIT,
}

_LOG_IN_EVENTS = {
  IamEvent.ORGANIZATION_ADMIN_ROOT_LOG_IN,
  IamEvent.USER_LOG_IN,
}

_REQUESTOR_EVENTS = ALL_IAM_EVENTS - _NO_REQUESTOR_EVENTS - _LOG_IN_EVENTS


class IamResponseStatus(object):
  SUCCESS = "success"
  FAILURE = "failure"


ALL_IAM_RESPONSE_STATUSES = {IamResponseStatus.SUCCESS, IamResponseStatus.FAILURE}


class IamLoggingService(Service):
  def _log_iam(
    self,
    event_name,
    request_parameters,
    response_element,
    response_status,
    requestor=None,
    event_time=None,
    event_id=None,
  ):
    assert response_status in ALL_IAM_RESPONSE_STATUSES, f"Unknown IamResponseStatus {response_status}"
    request_parameters = request_parameters or {}
    response_element = response_element or {}
    event_id = event_id or self.iam_event_id()
    if event_time is None:
      event_time = unix_timestamp()

    requestor_info = {}
    if requestor is not None:
      requestor_info = {
        "requestor": {
          "user_id": requestor.id,
          "user_email": requestor.email,
        }
      }

    self.services.logging_service.getLogger("sigopt.iam").info(
      json.dumps(
        {
          **requestor_info,
          "event_name": event_name,
          "request_parameters": request_parameters,
          "response_element": response_element,
          "response_status": response_status,
          "event_time": event_time,
          "event_id": event_id,
        }
      )
    )
    return event_id

  def log_iam(
    self,
    requestor,
    event_name,
    request_parameters,
    response_element,
    response_status,
    event_time=None,
    event_id=None,
  ):
    assert requestor and requestor.id and requestor.email, "Must have valid requestor"
    assert event_name in _REQUESTOR_EVENTS, f"Unknown IamEvent event {event_name}"
    self._log_iam(
      requestor=requestor,
      event_name=event_name,
      request_parameters=request_parameters,
      response_element=response_element,
      response_status=response_status,
    )

  # NOTE: user log in failures and rate-limiting will not have requestor
  def log_iam_no_requestor(
    self,
    event_name,
    request_parameters,
    response_element,
    response_status,
    event_time=None,
    event_id=None,
  ):
    assert event_name in _NO_REQUESTOR_EVENTS
    self._log_iam(
      event_name=event_name,
      request_parameters=request_parameters,
      response_element=response_element,
      response_status=response_status,
      event_time=event_time,
      event_id=event_id,
    )

  def log_iam_log_in(
    self,
    event_name,
    request_parameters,
    response_element,
    response_status,
    event_time=None,
    event_id=None,
    requestor=None,
  ):
    assert event_name in _LOG_IN_EVENTS
    if response_status == IamResponseStatus.SUCCESS:
      assert requestor and requestor.id and requestor.email, "Successful logins must have valid requestor"
    else:
      assert requestor is None, "Failed logins cannot have a requestor"
    self._log_iam(
      requestor=requestor,
      event_name=event_name,
      request_parameters=request_parameters,
      response_element=response_element,
      response_status=response_status,
      event_time=event_time,
      event_id=event_id,
    )

  @classmethod
  def iam_event_id(cls):
    return str(uuid.uuid4())
