# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.handlers.validate.membership import validate_membership_type
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.json.builder import MembershipJsonBuilder, PaginationJsonBuilder
from zigopt.membership.model import Membership
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN


class OrganizationsMembershipsListDetailHandler(OrganizationHandler):
  authenticator = api_token_authentication
  # NOTE: ADMIN because normal users on a client in an organization don't need to be
  # able to see which users are in the org
  # There are currently no pages on the website accessible to a normal user that show the users
  # in an organization
  required_permissions = ADMIN

  Params = ImmutableStruct("Params", ("membership_type",))

  def parse_params(self, request):
    data = request.params()
    membership_type = get_opt_with_validation(data, "membership_type", ValidationType.string)
    membership_type = validate_membership_type(membership_type)
    return self.Params(membership_type)

  def handle(self, params):  # type: ignore
    assert self.organization is not None

    query = self.services.database_service.query(Membership).filter_by(organization_id=self.organization.id)

    if params.membership_type:
      query = query.filter_by(membership_type=params.membership_type)

    memberships = self.services.database_service.all(query)

    user_ids = [membership.user_id for membership in memberships]
    users = self.services.user_service.find_by_ids(user_ids)
    user_map = to_map_by_key(users, lambda u: u.id)

    return PaginationJsonBuilder(
      data=[
        MembershipJsonBuilder(
          membership,
          self.organization,
          user_map[membership.user_id],
        )
        for membership in memberships
        if membership.user_id in user_map
      ]
    )
