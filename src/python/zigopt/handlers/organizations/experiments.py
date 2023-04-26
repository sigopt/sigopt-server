# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.list_base import BaseExperimentsListHandler
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN


class OrganizationsExperimentsListDetailHandler(OrganizationHandler, BaseExperimentsListHandler):
  authenticator = api_token_authentication
  # NOTE: ADMIN because normal users on a client in an organization should not be
  # able to see all the organization's experiments.
  required_permissions = ADMIN

  def handle(self, params):
    assert self.organization is not None

    client_ids = [c.id for c in self.services.client_service.find_by_organization_id(self.organization.id)]
    return self.do_handle(params, client_ids, params.user)
