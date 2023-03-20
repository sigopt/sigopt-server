# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.json.builder import OrganizationJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ, TokenMeta


class OrganizationsDetailHandler(OrganizationHandler):
  authenticator = api_token_authentication
  allow_development = True
  required_permissions = READ
  permitted_scopes = (TokenMeta.ALL_ENDPOINTS, TokenMeta.SIGNUP_SCOPE)

  def handle(self):
    return OrganizationJsonBuilder.json(
      self.organization,
      optimized_runs_in_billing_cycle=self.services.organization_service.get_optimized_runs_from_organization_id(
        self.organization.id
      ),
      data_storage_bytes=self.services.file_service.count_bytes_used_by_organization(self.organization.id),
      total_runs_in_billing_cycle=self.services.organization_service.get_total_runs_from_organization_id(
        self.organization.id
      ),
    )
