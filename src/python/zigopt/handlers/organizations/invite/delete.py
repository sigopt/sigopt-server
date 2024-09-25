# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import user_token_authentication
from zigopt.brand.constant import PRODUCT_NAME
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.handlers.validate.base import validate_email
from zigopt.handlers.validate.validate_dict import ValidationType, get_with_validation
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN

from libsigopt.aux.errors import SigoptValidationError


class OrganizationsUninviteHandler(OrganizationHandler):
  authenticator = user_token_authentication
  required_permissions = ADMIN

  Params = ImmutableStruct("Params", ("email",))

  def parse_params(self, request):
    data = request.params()
    email = get_with_validation(data, "email", ValidationType.string)
    email = validate_email(email)
    return OrganizationsUninviteHandler.Params(email=email)

  def handle(self, params):  # type: ignore
    assert self.auth is not None
    assert self.organization is not None

    email = params.email
    invitee = self.services.user_service.find_by_email(email)
    self.check_can_uninvite(email=email)

    if invitee:
      self.services.permission_service.delete_by_organization_and_user(self.organization.id, invitee.id)
      self.services.membership_service.delete_by_organization_and_user(self.organization.id, invitee.id)
      self.services.iam_logging_service.log_iam(
        requestor=self.auth.current_user,
        event_name=IamEvent.MEMBERSHIP_DELETE,
        request_parameters={
          "user_id": invitee.id,
          "organization_id": self.organization.id,
        },
        response_element={},
        response_status=IamResponseStatus.SUCCESS,
      )

    self.services.pending_permission_service.delete_by_email_and_organization(email, self.organization)
    self.services.invite_service.delete_by_email_and_organization(email, self.organization.id)
    return {}

  def check_can_uninvite(self, email):
    assert self.auth is not None
    assert self.organization is not None

    uninvitee = self.services.user_service.find_by_email(email)
    invite = self.services.invite_service.find_by_email_and_organization(email, self.organization.id)

    if not uninvitee and not invite:
      raise SigoptValidationError(f"No invite exists for the email address {email}")

    if uninvitee and self.services.membership_service.user_is_owner_for_organization(
      user_id=uninvitee.id,
      organization_id=self.organization.id,
    ):
      raise SigoptValidationError(
        "Once it has been accepted, the invite of an organization's owner cannot be modified."
        f" Please see your {PRODUCT_NAME} account team."
      )

    if uninvitee and uninvitee.id == self.auth.current_user.id:
      raise SigoptValidationError("You cannot modify your own role")
