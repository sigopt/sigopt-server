# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import user_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.handlers.validate.base import validate_email_domain
from zigopt.handlers.validate.organization import validate_organization_name
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.json.builder import OrganizationJsonBuilder
from zigopt.net.errors import NotFoundError
from zigopt.organization.model import Organization
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, WRITE

from libsigopt.aux.errors import SigoptValidationError


class OrganizationsUpdateHandler(OrganizationHandler):
  authenticator = user_token_authentication
  required_permissions = ADMIN

  Params = ImmutableStruct(
    "Params",
    (
      "allow_signup_from_email_domains",
      "client_for_email_signup",
      "email_domains",
      "name",
    ),
  )

  def parse_params(self, request):
    assert self.organization is not None

    data = request.params()
    name = get_opt_with_validation(data, "name", ValidationType.string)
    name = validate_organization_name(name) if name else None
    client_for_email_signup = get_opt_with_validation(data, "client_for_email_signup", ValidationType.id)
    allow_signup_from_email_domains = get_opt_with_validation(
      data,
      "allow_signup_from_email_domains",
      ValidationType.boolean,
    )
    email_domains = get_opt_with_validation(data, "email_domains", ValidationType.arrayOf(ValidationType.string))
    if email_domains:
      email_domains = [validate_email_domain(domain) for domain in email_domains]

    did_enable_allow_signup = (
      allow_signup_from_email_domains and not self.organization.organization_meta.allow_signup_from_email_domains
    )
    if did_enable_allow_signup and not self.services.email_verification_service.enabled:
      raise SigoptValidationError("Email verification is disabled, so signup from email domains cannot be enabled.")

    return OrganizationsUpdateHandler.Params(
      name=name,
      email_domains=email_domains,
      client_for_email_signup=client_for_email_signup,
      allow_signup_from_email_domains=allow_signup_from_email_domains,
    )

  def handle(self, params):
    assert self.auth is not None
    assert self.organization is not None

    update_clause = {}

    if params.name is not None:
      update_clause[Organization.name] = params.name
      self.organization.name = params.name

    meta = self.organization.organization_meta.copy_protobuf()

    if params.email_domains is not None:
      meta.email_domains[:] = params.email_domains

    if params.allow_signup_from_email_domains is not None:
      meta.allow_signup_from_email_domains = params.allow_signup_from_email_domains

    if params.client_for_email_signup is not None:
      client = self.services.client_service.find_by_id(params.client_for_email_signup)
      if (
        client
        and client.organization_id == self.organization.id
        and self.auth.can_act_on_client(self.services, requested_permission=WRITE, client=client)
      ):
        meta.client_for_email_signup = params.client_for_email_signup
      else:
        raise NotFoundError(f"Invalid client ID: {params.client_for_email_signup}")

    if meta.allow_signup_from_email_domains and not meta.email_domains:
      raise SigoptValidationError("If `allow_signup_from_email_domains` is true, `email_domains` must be non-empty")

    if meta != self.organization.organization_meta:
      self.organization.organization_meta = meta
      update_clause[Organization.organization_meta] = meta

    if update_clause:
      self.services.database_service.update_one(
        self.services.database_service.query(Organization).filter_by(id=self.organization.id),
        update_clause,
      )

    optimized_runs_in_billing_cycle = self.services.organization_service.get_optimized_runs_from_organization_id(
      self.organization.id
    )
    data_storage = self.services.file_service.count_bytes_used_by_organization(self.organization.id)
    total_runs_in_billing_cycle = self.services.organization_service.get_total_runs_from_organization_id(
      self.organization.id
    )

    organization_json = OrganizationJsonBuilder.json(
      self.organization,
      optimized_runs_in_billing_cycle=optimized_runs_in_billing_cycle,
      data_storage_bytes=data_storage,
      total_runs_in_billing_cycle=total_runs_in_billing_cycle,
    )
    self.services.iam_logging_service.log_iam(
      requestor=self.auth.current_user,
      event_name=IamEvent.ORGANIZATION_UPDATE,
      # TODO(SN-987): refactor some of this code to stop repeating all these attributes everywhere
      request_parameters=compact(
        {
          "organization_id": self.organization.id,
          "allow_signup_from_email_domains": params.allow_signup_from_email_domains,
          "client_for_email_signup": params.client_for_email_signup,
          "email_domains": params.email_domains,
          "name": params.name,
        }
      ),
      response_element=organization_json,
      response_status=IamResponseStatus.SUCCESS,
    )
    return organization_json
