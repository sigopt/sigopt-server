# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication, user_token_authentication
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.clients.base import ClientHandler
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.training_runs.base import TrainingRunHandler
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.json.builder import PaginationJsonBuilder, TokenJsonBuilder
from zigopt.net.errors import ForbiddenError, NotFoundError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE, TokenMeta
from zigopt.protobuf.lib import copy_protobuf

from libsigopt.aux.errors import SigoptValidationError


class TokenHandler(Handler):
  def __init__(self, services, request, token):
    if token is None:
      raise Exception("Token value required")

    self.token_value = token
    self.token = None
    super().__init__(services, request)

  def find_objects(self):
    return extend_dict(super().find_objects(), {"token": self._find_token(self.token_value)})

  def _find_token(self, token_value):
    assert self.auth is not None

    if token_value == "self":
      token = self.auth.api_token
    else:
      token = self.services.token_service.find_by_token(token_value, include_expired=False)
    if token:
      return token
    raise NotFoundError("Token not found")

  def can_act_on_objects(self, requested_permission, objects):
    assert self.auth is not None

    return super().can_act_on_objects(requested_permission, objects) and self.auth.can_act_on_token(
      self.services, requested_permission, objects["token"]
    )


class ClientsTokensDeleteHandler(TokenHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  def handle(self):
    assert self.token is not None
    if not self.token.expiration_timestamp and self.token.all_experiments:
      raise ForbiddenError("Cannot delete root token")
    if self.services.token_service.delete_token(self.token):
      return {}
    raise NotFoundError("Token not found")


class ClientsTokensUpdateHandler(TokenHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE

  Params = ImmutableStruct("Params", ("token", "lasts_forever", "expires"))

  def parse_params(self, request):
    data = request.params()
    return self.Params(
      token=get_opt_with_validation(data, "token", ValidationType.string),
      lasts_forever=get_opt_with_validation(data, "lasts_forever", ValidationType.boolean),
      expires=get_opt_with_validation(data, "expires", ValidationType.string),
    )

  def handle(self, params):
    assert self.auth is not None
    assert self.token is not None

    if (new_token_value := params.token) is not None:
      if new_token_value != "rotate":
        raise SigoptValidationError('Token must equal "rotate"')
      self.services.token_service.rotate_token(self.token)
    if params.lasts_forever is not None:
      meta = copy_protobuf(self.token.meta)
      meta.lasts_forever = params.lasts_forever
      self.services.token_service.update_meta(self.token, meta)
    if (new_expires_value := params.expires) is not None:
      if new_expires_value != "renew":
        raise SigoptValidationError('Expires must equal "renew"')
      if self.token.meta.can_renew:
        self.services.token_service.renew_token(self.token)
      else:
        raise ForbiddenError("Token cannot be renewed")
    client = self.services.client_service.find_by_id(self.token.client_id, current_client=self.auth.current_client)
    return TokenJsonBuilder.json(self.token, client)


class ClientsTokensDetailHandler(TokenHandler):
  allow_development = True
  authenticator = api_token_authentication
  required_permissions = READ
  permitted_scopes = (TokenMeta.ALL_ENDPOINTS, TokenMeta.SHARED_EXPERIMENT_SCOPE)

  def handle(self):
    assert self.auth is not None
    assert self.token is not None

    client = self.services.client_service.find_by_id(self.token.client_id, current_client=self.auth.current_client)
    return TokenJsonBuilder.json(self.token, client)


class ExperimentsTokensCreateHandler(ExperimentHandler):
  authenticator = api_token_authentication
  allow_development = False
  required_permissions = WRITE

  def handle(self):
    assert self.auth is not None
    assert self.experiment is not None

    if not self.services.config_broker.get("features.shareLinks", True):
      raise ForbiddenError("You cannot create guest tokens.")

    token = self.services.token_service.create_guest_experiment_token(
      self.experiment.client_id,
      self.experiment.id,
      creating_user_id=(self.auth.current_user and self.auth.current_user.id),
      session_expiration=self.auth.session_expiration,
    )
    assert token and self.auth.can_act_on_token(self.services, READ, token)
    client = self.services.client_service.find_by_id(token.client_id, current_client=self.auth.current_client)
    return TokenJsonBuilder.json(token, client)


class TrainingRunsTokensCreateHandler(TrainingRunHandler):
  authenticator = api_token_authentication
  allow_development = False
  required_permissions = WRITE

  def handle(self):
    assert self.auth is not None
    assert self.training_run is not None

    if not self.services.config_broker.get("features.shareLinks", True):
      raise ForbiddenError("You cannot create guest tokens.")
    token = self.services.token_service.create_guest_training_run_token(
      client_id=self.training_run.client_id,
      training_run_id=self.training_run.id,
      experiment_id=self.training_run.experiment_id,
      creating_user_id=(self.auth.current_user and self.auth.current_user.id),
      session_expiration=self.auth.session_expiration,
    )
    assert token and self.auth.can_act_on_token(self.services, READ, token)
    client = self.services.client_service.find_by_id(token.client_id, current_client=self.auth.current_client)
    return TokenJsonBuilder.json(token, client)


class ClientsTokensCreateHandler(ClientHandler):
  authenticator = user_token_authentication
  required_permissions = ADMIN

  auth: EmptyAuthorization

  def handle(self):
    assert self.auth is not None
    assert self.client is not None
    token = self.services.token_service.get_or_create_client_signup_token(
      self.client.id,
      creating_user_id=self.auth.current_user.id,
    )
    assert token and self.auth.can_act_on_token(self.services, READ, token)
    return TokenJsonBuilder.json(token, self.client)


class ClientsTokensListDetailHandler(ClientHandler):
  authenticator = user_token_authentication
  required_permissions = READ

  # Ensure that the user has a role token, since users who were created before the introduction
  # of role tokens might not have one yet
  def ensure_includes_role_token(self, tokens):
    assert self.auth is not None
    auth = self.auth
    assert self.client is not None
    client = self.client
    if (role_token := find(
      tokens,
      lambda t: t.user_id == auth.current_user.id and t.client_id == client.id and t.development is False,
    )) is None:
      role_token = self.services.token_service.get_or_create_role_token(
        self.client.id,
        self.auth.current_user.id,
      )
      return tokens + [role_token]
    return tokens

  def ensure_includes_development_role_token(self, tokens):
    assert self.auth is not None
    current_user = self.auth.current_user
    assert current_user is not None
    assert self.client is not None
    client = self.client
    if (development_token := find(
      tokens,
      lambda t: t.user_id == current_user.id and t.client_id == client.id and t.development is True,
    )) is None:
      development_token = self.services.token_service.get_or_create_development_role_token(
        self.client.id,
        self.auth.current_user.id,
      )
      return tokens + [development_token]
    return tokens

  def handle(self):
    assert self.auth is not None
    assert self.client is not None
    created_guest_tokens = self.services.token_service.find_guest_tokens(
      client_id=self.client.id,
      creating_user_id=self.auth.current_user.id,
    )
    my_tokens = self.services.token_service.find_by_client_and_user(
      client_id=self.client.id,
      user_id=self.auth.current_user.id,
    )
    my_tokens = self.ensure_includes_role_token(my_tokens)
    my_tokens = self.ensure_includes_development_role_token(my_tokens)
    tokens = [*created_guest_tokens, *my_tokens]
    assert all(self.auth.can_act_on_token(self.services, READ, t) for t in tokens)
    return PaginationJsonBuilder([TokenJsonBuilder(t, self.client) for t in tokens])
