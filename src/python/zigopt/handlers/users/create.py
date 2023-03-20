# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import maybe_client_token_authentication
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.validate.client import validate_client_name
from zigopt.handlers.validate.user import validate_user_email, validate_user_name, validate_user_password
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation, get_with_validation
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.json.builder import UserJsonBuilder
from zigopt.membership.model import MembershipType
from zigopt.net.errors import BadParamError, ConflictingDataError, ForbiddenError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import NONE, READ, TokenMeta
from zigopt.protobuf.gen.user.usermeta_pb2 import UserMeta
from zigopt.user.model import User


class BaseUsersCreateHandler(Handler):
  UserAttributes = ImmutableStruct(
    "UserAttributes",
    (
      "name",
      "email",
      "plaintext_password",
      "edu",
      "client_name",
      "public_cert",
    ),
  )

  def _validate_can_signup_to_client(self, email, requested_client_id):
    # NOTE: We require client authentication to check that the requested client supports directly signing up.
    # This is not strictly needed, since we revalidate after the user verifies their email in case the org has changed.
    # However, we want to give a sane error message when direct sign-up is disabled,
    # and we can't do that without leaking information about the client (notably, it's configured email domains).
    if not self.services.email_verification_service.enabled:
      raise ForbiddenError("Directly joining clients is not supported because email verification is disabled.")

    requested_client = (
      self.auth.current_client
      if napply(self.auth.current_client, lambda c: c.id) == requested_client_id
      else self.services.client_service.find_by_id(requested_client_id)
    )
    requested_organization = napply(
      requested_client, lambda c: self.services.organization_service.find_by_id(c.organization_id)
    )

    if (
      requested_client
      and self.auth.can_act_on_client(self.services, READ, requested_client)
      and requested_organization
      and self.auth.can_act_on_organization(self.services, READ, requested_organization)
      and self.services.invite_service.email_is_permitted_by_client_for_direct_signup(
        organization=requested_organization,
        client=requested_client,
        email=email,
      )
    ):
      pending_client = requested_client
      return pending_client
    raise ForbiddenError("You do not have permission to join the requested client")

  def create_user_by_invite(self, user_attributes, verified_invite, has_verified_email):
    user = self.create_user_model_without_save(
      user_attributes,
      has_verified_email=has_verified_email,
      pending_client_id=None,
    )
    inviter = self.services.user_service.find_by_id(verified_invite.inviter)

    # TODO(SN-1098): I believe all of these checks are no longer needed, since they are
    # checked in invite_service.invite_is_still_valid
    if verified_invite.membership_type == MembershipType.owner:
      is_owner = self.services.membership_service.user_is_owner_for_organization(
        user_id=verified_invite.inviter,
        organization_id=verified_invite.organization_id,
      )
      if not is_owner:
        raise ForbiddenError("Owners must be invited by organization owners.")
    else:
      membership = self.services.membership_service.find_by_user_and_organization(
        user_id=inviter.id, organization_id=verified_invite.organization_id
      )
      if membership is None:
        raise ForbiddenError("You must be invited by a member of your organization.")
    self.services.user_service.create_new_user(user)
    self.send_welcome_email(user)
    return user

  def create_user_by_self_signup(self, user_attributes, pending_client, has_verified_email=False):
    if self.services.config_broker.get("features.requireInvite", False):
      raise ForbiddenError("You must be invited by an administrator to sign up.")
    user = self.create_user_model_without_save(
      user_attributes,
      has_verified_email=has_verified_email,
      pending_client_id=napply(pending_client, lambda c: c.id),
    )
    if has_verified_email:
      self.services.user_service.create_new_user(user)
      self.send_welcome_email(user)
    else:
      email_verification_code = self.services.email_verification_service.set_email_verification_code_without_save(user)
      self.services.user_service.create_new_user(user)
      self.services.email_verification_service.send_verification_email(user, email_verification_code)
    return user

  def track_user_creation(
    self,
    user,
    user_attributes,
    was_invited,
  ):
    # TODO(SN-1099): Currently we're setting client and permission as one of the multiple that were created,
    # but we could do something more precise.
    membership = list_get(self.services.membership_service.find_by_user_id(user_id=user.id), 0)
    permission = napply(membership, lambda m: list_get(self.services.permission_service.find_by_membership(m), 0))
    client = napply(permission, lambda p: self.services.client_service.find_by_id(p.client_id))
    organization = napply(client, lambda c: self.services.organization_service.find_by_id(c.organization_id))

    properties = {
      "invited": was_invited,
    }
    if organization:
      properties["organization_id"] = organization.id
      properties["organization_name"] = organization.name
    self.services.iam_logging_service.log_iam(
      requestor=user,
      event_name=IamEvent.USER_CREATE,
      request_parameters={
        "name": user_attributes.name,
        "email": user_attributes.email,
        "client_name": user_attributes.client_name,
        "public_cert": user_attributes.public_cert,
        "edu": user_attributes.edu,
      },
      response_element=UserJsonBuilder.json(user),
      response_status=IamResponseStatus.SUCCESS,
    )

  def create_clients_and_permissions(self, user, verified_invite):
    # NOTE: If the user is claiming a guest client *AND* receiving an invite,
    # then this block overrides the `client` variable from the above, which is what we want
    assert verified_invite is not None
    self.services.invite_service.create_memberships_and_permissions_from_invites(
      user,
      [verified_invite],
      requestor=user,
    )
    self.services.pending_permission_service.delete_by_invite_id(verified_invite.id)
    self.services.invite_service.delete_by_email(user.email)

  def send_welcome_email(self, user):
    self.services.email_router.send(self.services.email_templates.welcome_email(user))

  def get_verified_invite(self, email, invite_code):
    unvalidated_invites = self.services.invite_service.find_by_email(email, valid_only=False)
    claimable_invites = [
      invite
      for invite in unvalidated_invites
      if invite.invite_code == invite_code or (not self.services.email_verification_service.enabled)
    ]
    # TODO(SN-1100): This doesn't handle multiple invite codes. We probably don't need to
    claimable_invite = list_get(claimable_invites, 0)
    if claimable_invite:
      if self.services.invite_service.invite_is_valid(claimable_invite):
        return claimable_invite
      else:
        raise ForbiddenError("This invite is no longer valid.")
    if invite_code and claimable_invite is None:
      provided_invite = self.services.invite_service.find_by_code(invite_code)
      if provided_invite is not None and email != provided_invite.email:
        raise ConflictingDataError(f"This invite can only be used with the email address: {provided_invite.email}.")
      raise BadParamError("Invalid invite_code")
    return claimable_invite

  def create_user_model_without_save(self, user_attributes, has_verified_email, pending_client_id):
    meta = UserMeta()
    if user_attributes.email.endswith(".edu") or user_attributes.edu:
      meta.educational_user = True
    if user_attributes.public_cert:
      meta.public_cert = user_attributes.public_cert
    meta.date_created = unix_timestamp()
    meta.has_verified_email = has_verified_email
    meta.SetFieldIfNotNone("pending_client_name", user_attributes.client_name)
    meta.SetFieldIfNotNone("pending_client_id", pending_client_id)
    meta.show_welcome = True
    return User(
      name=user_attributes.name,
      email=user_attributes.email,
      plaintext_password=user_attributes.plaintext_password,
      user_meta=meta,
    )


class UsersCreateHandler(BaseUsersCreateHandler):
  authenticator = maybe_client_token_authentication
  required_permissions = NONE
  permitted_scopes = (TokenMeta.ALL_ENDPOINTS, TokenMeta.SIGNUP_SCOPE)

  Params = ImmutableStruct("Params", ("user_attributes", "invite_code", "pending_client", "has_verified_email"))

  def parse_params(self, request):
    data = request.params()
    email = validate_user_email(get_with_validation(data, "email", ValidationType.string))
    client_name = get_opt_with_validation(data, "client_name", ValidationType.string)
    client_name = validate_client_name(client_name) if client_name else None
    invite_code = get_opt_with_validation(data, "invite_code", ValidationType.string)
    requested_client_id = get_opt_with_validation(data, "client", ValidationType.id)
    name = validate_user_name(get_with_validation(data, "name", ValidationType.string))
    plaintext_password = validate_user_password(get_with_validation(data, "password", ValidationType.string))
    edu = get_opt_with_validation(data, "edu", ValidationType.boolean) or False

    if requested_client_id:
      if invite_code:
        raise BadParamError("Cannot provide both `client` and `invite_code`")
      pending_client = self._validate_can_signup_to_client(email, requested_client_id)
    else:
      pending_client = None

    return UsersCreateHandler.Params(
      user_attributes=self.UserAttributes(
        name=name,
        email=email,
        plaintext_password=plaintext_password,
        edu=edu,
        client_name=client_name,
        public_cert=None,
      ),
      invite_code=invite_code,
      pending_client=pending_client,
      has_verified_email=False,
    )

  def handle(self, params):
    verified_invite = self.get_verified_invite(params.user_attributes.email, params.invite_code)
    if verified_invite:
      has_verified_email = params.has_verified_email or verified_invite.invite_code == params.invite_code
      user = self.create_user_by_invite(params.user_attributes, verified_invite, has_verified_email)
      self.create_clients_and_permissions(user, verified_invite)
    else:
      user = self.create_user_by_self_signup(params.user_attributes, params.pending_client, params.has_verified_email)
    self.track_user_creation(user, params.user_attributes, was_invited=bool(verified_invite))
    return UserJsonBuilder.json(user)
