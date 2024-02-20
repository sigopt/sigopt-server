# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections.abc import Sequence

from zigopt.common import *
from zigopt.api.auth import api_token_authentication, login_authentication
from zigopt.client.model import Client
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.json.builder import SessionJsonBuilder, UserJsonBuilder
from zigopt.json.session import Session
from zigopt.net.errors import ForbiddenError, NotFoundError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import NONE, READ, TokenMeta


class BaseSessionHandler(Handler):
  def get_client_for_user(self, user, preferred_client_id=None):
    assert self.auth is not None

    memberships = self.services.membership_service.find_by_user_id(user.id)
    clients: Sequence[Client] = self.services.client_service.find_clients_in_organizations_visible_to_user(
      user,
      memberships,
    )
    if (client := find(clients, lambda c: c.id == preferred_client_id)) is None:
      client = min(clients, key=lambda c: (c.id if c else 0), default=None)

    if client:
      if not self.auth.can_act_on_client(self.services, READ, client):
        self.services.exception_logger.soft_exception(
          msg="Assigning user to unavailable client",
          extra=dict(user_id=user.id, client_id=client.id),
        )
        client = None
    return client

  def verify_email(self, user):
    assert self.auth is not None

    # NOTE: Important to set has_email_verified up front, since the invite logic
    # checks that the user has verified their email. We make sure to pull off the pending_client_id
    # first since that field is cleared when the email is verified
    pending_client_id = user.user_meta.pending_client_id
    pending_client_name = user.user_meta.pending_client_name
    self.services.email_verification_service.declare_email_verified(user)

    # TODO: This could be done as a batch insert, but in practice this
    # probably won't be a problem
    valid_invites = self.services.invite_service.find_by_email(user.email, valid_only=True)

    client: Client | None = None

    # NOTE: If the user has a pending_client_id or outstanding invites, attempt to
    # add them to the client.
    # TODO: More of this could be shared with POST /users/X/permissions if we wanted.
    # Specifically, that endpoint couLd also be used to create permissions from outstanding
    # invites as well, so there is only one flow for attempting to join a Client.
    if valid_invites:
      clients = self.services.invite_service.create_memberships_and_permissions_from_invites(
        user,
        valid_invites,
        self.auth.current_user,
      )
      (_, _, client) = list_get(clients, 0) or (None, None, None)
    elif pending_client_id:
      pending_client = self.services.client_service.find_by_id(pending_client_id)
      if pending_client:
        pending_organization = self.services.organization_service.find_by_id(pending_client.organization_id)
        if pending_organization:
          did_signup, _ = self.services.invite_service.signup_to_client_if_permitted(
            user=user,
            organization=pending_organization,
            client=pending_client,
          )
          if did_signup:
            client = pending_client

    if not client:
      client = self.get_client_for_user(user)
    if not client:
      if not self.services.config_broker.get("features.allowCreateOrganization", False):
        raise ForbiddenError("You must be invited to an organization")
      name = pending_client_name or user.name
      (_, client) = self.services.organization_service.set_up_new_organization(
        organization_name=name,
        client_name=name,
        user=user,
        allow_users_to_see_experiments_by_others=None,
        academic=user.user_meta.educational_user,
        user_is_owner=True,
        requestor=self.auth.current_user,
      )

    self.services.pending_permission_service.delete_by_email(user.email)
    self.services.invite_service.delete_by_email(user.email)

    return client

  def user_session(self, user_token, user=None, client=None, preferred_client_id=None):
    if user:
      client = client or self.get_client_for_user(user, preferred_client_id=preferred_client_id)

    code = self.services.user_service.set_password_reset_code(user) if user and user.needs_password_reset else None

    return Session(
      api_token=user_token,
      client=client,
      code=code,
      needs_password_reset=bool(user and user.needs_password_reset),
      user=user,
    )

  def log_iam_log_in_success(self, user):
    assert self.auth is not None

    event_names = [IamEvent.USER_LOG_IN]
    if self.services.membership_service.find_owners_by_user_id(user.id):
      event_names.append(IamEvent.ORGANIZATION_ADMIN_ROOT_LOG_IN)
    for event_name in event_names:
      self.services.iam_logging_service.log_iam_log_in(
        requestor=self.auth.current_user,
        event_name=event_name,
        request_parameters={"user_id": user.id},
        # NOTE: avoid logging sensitive data in the Session by just logging User instead
        response_element=UserJsonBuilder.json(user),
        response_status=IamResponseStatus.SUCCESS,
      )


class CreateSessionHandler(BaseSessionHandler):
  authenticator = login_authentication
  required_permissions = NONE

  def handle(self):
    assert self.auth is not None

    user = self.auth.current_user
    client = None
    if self.auth.authenticated_from_email_link:
      client = self.verify_email(user)
    self.log_iam_log_in_success(user)
    return SessionJsonBuilder.json(
      self.user_session(
        self.auth.api_token,
        user=user,
        client=client,
      )
    )


class SessionHandler(BaseSessionHandler):
  allow_development = True
  authenticator = api_token_authentication
  required_permissions = NONE
  permitted_scopes = (TokenMeta.ALL_ENDPOINTS, TokenMeta.SIGNUP_SCOPE)

  def parse_params(self, request):
    preferred_client_id = get_opt_with_validation(request.params(), "preferred_client_id", ValidationType.id)
    return preferred_client_id

  def handle(self, preferred_client_id):
    assert self.auth is not None

    if self.auth.api_token:
      return SessionJsonBuilder.json(
        self.user_session(
          self.auth.api_token,
          user=self.auth.current_user,
          client=self.auth.current_client,
          preferred_client_id=preferred_client_id,
        )
      )
    raise NotFoundError()
