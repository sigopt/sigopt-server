# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.authorization.client import ClientAuthorization
from zigopt.client.model import Client
from zigopt.experiment.model import Experiment
from zigopt.membership.model import Membership, MembershipType
from zigopt.permission.model import Permission
from zigopt.protobuf.gen.client.clientmeta_pb2 import ClientMeta
from zigopt.protobuf.gen.permission.permissionmeta_pb2 import PermissionMeta
from zigopt.protobuf.gen.user.usermeta_pb2 import UserMeta
from zigopt.suggestion.model import Suggestion
from zigopt.suggestion.processed.model import ProcessedSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion
from zigopt.token.model import Token
from zigopt.token.token_types import TokenType
from zigopt.user.model import User

from sigopttest.base.utils import generate_ids


ORGANIZATION_FIELDS = [
  "created",
  "id",
  "academic",
  "name",
  "optimized_runs_in_billing_cycle",
  "data_storage_bytes",
  "total_runs_in_billing_cycle",
]

VISIBLE_CLIENT_FIELDS = [
  "client_security",
  "created",
  "id",
  "name",
  "organization",
]

HIDDEN_CLIENT_FIELDS = ["deleted"]

VISIBLE_USER_FIELDS = [
  "created",
  "deleted",
  "email",
  "has_verified_email",
  "id",
  "name",
  "planned_usage",
  "show_welcome",
]

HIDDEN_USER_FIELDS = [
  "educational_user",
]

VISIBLE_SUGGESTION_FIELDS = [
  "assignments",
  "created",
  "deleted",
  "experiment",
  "id",
  "metadata",
  "state",
]

ids = generate_ids()


class BuilderTestBase(object):
  client_id = next(ids)
  organization_id = next(ids)
  user_id = next(ids)

  @pytest.fixture
  def client(self):
    client_meta = ClientMeta()
    client_meta.date_created = 216097
    client_meta.client_security.allow_users_to_see_experiments_by_others = True
    return Client(
      id=self.client_id,
      organization_id=self.organization_id,
      client_meta=client_meta,
    )

  @pytest.fixture
  def client_token(self, client):
    return Token(client_id=client.id, token_type=TokenType.CLIENT_API)

  @pytest.fixture
  def client_authorization(self, client, client_token):
    return ClientAuthorization(client, client_token)

  def make_user(self, name, email):
    user_meta = UserMeta()
    user_meta.date_created = 212887
    user_meta.educational_user = False
    user_meta.has_verified_email = True
    user_meta.show_welcome = True
    return User(
      id=self.user_id,
      name=name,
      email=email,
      user_meta=user_meta,
    )

  @pytest.fixture
  def user(self):
    return self.make_user(
      name="Builder Test Mock User",
      email="usermock@buildertest.py",
    )

  @pytest.fixture
  def populated_experiment_list(self):
    return [f"exp{i}" for i in range(5)]

  @pytest.fixture
  def empty_experiment_list(self):
    return []

  def make_permission(
    self,
    can_admin=False,
    can_read=False,
    can_see_experiments_by_others=True,
    can_write=False,
  ):
    permission_meta = PermissionMeta()
    permission_meta.can_admin = can_admin
    permission_meta.can_read = can_read
    permission_meta.can_write = can_write
    permission_meta.can_see_experiments_by_others = can_see_experiments_by_others
    return Permission(
      user_id=self.user_id,
      client_id=self.client_id,
      organization_id=self.organization_id,
      permission_meta=permission_meta,
    )

  @pytest.fixture
  def read_permission(self):
    return self.make_permission(can_read=True)

  @pytest.fixture
  def write_permission(self):
    return self.make_permission(can_read=True, can_write=True)

  @pytest.fixture
  def admin_permission(self):
    return self.make_permission(can_admin=True, can_read=True, can_write=True)

  @pytest.fixture
  def membership(self):
    return Membership(user_id=self.user_id, organization_id=self.organization_id, membership_type=MembershipType.owner)

  @pytest.fixture
  def experiment(self):
    return Experiment(id=5)

  @pytest.fixture
  def unprocessed(self, experiment):
    return UnprocessedSuggestion(
      id=3,
      experiment_id=experiment.id,
      source=UnprocessedSuggestion.Source.GP_CATEGORICAL,
    )

  @pytest.fixture
  def processed(self, experiment, unprocessed):
    return ProcessedSuggestion(
      experiment_id=experiment.id,
      suggestion_id=unprocessed.id,
    )

  @pytest.fixture
  def suggestion(self, unprocessed, processed):
    return Suggestion(
      unprocessed=unprocessed,
      processed=processed,
    )
