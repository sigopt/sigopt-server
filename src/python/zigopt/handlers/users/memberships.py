# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.users.base import UserHandler
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.json.builder import MembershipJsonBuilder, PaginationJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class UsersMembershipsListDetailHandler(UserHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  Params = ImmutableStruct("Params", ("organization",))

  def parse_params(self, request):
    data = request.params()
    organization_id = get_opt_with_validation(data, "organization", ValidationType.id)
    organization = None
    if organization_id:
      organization = self.services.organization_service.find_by_id(organization_id)
    return self.Params(organization=organization)

  def handle(self, params):
    assert self.user is not None

    memberships = []
    if params.organization:
      single_membership = self.services.membership_service.find_by_user_and_organization(
        self.user.id, params.organization.id
      )
      memberships = [single_membership] if single_membership else []
    else:
      memberships = self.services.membership_service.find_by_user_id(self.user.id)

    organization_ids = [membership.organization_id for membership in memberships]
    organizations = self.services.organization_service.find_by_ids(organization_ids)
    organization_map = to_map_by_key(organizations, lambda o: o.id)

    return PaginationJsonBuilder(
      data=[
        MembershipJsonBuilder(
          membership,
          organization_map[membership.organization_id],
          self.user,
        )
        for membership in memberships
        if membership.organization_id in organization_map
      ]
    )
