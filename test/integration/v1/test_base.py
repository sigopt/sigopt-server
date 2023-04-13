# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import copy

import pytest

from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.sigopt_datetime import current_datetime, datetime_to_seconds
from zigopt.experiment.model import Experiment
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.experiments.observations.create import CreatesObservationsMixin
from zigopt.handlers.validate.observation import validate_observation_json_dict_for_create
from zigopt.membership.model import MembershipType
from zigopt.observation.model import Observation
from zigopt.protobuf.gen.observation.observationdata_pb2 import ObservationData
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE

from integration.auth import AuthProvider
from integration.base import BaseTest
from integration.connection import IntegrationTestConnection
from integration.utils.emails import extract_verify_code


class Connection:
  def __init__(
    self, sigopt_connection, client_id, organization_id, user_id=None, email=None, password=None, development=False
  ):
    self.conn = sigopt_connection
    self.client_id = client_id
    self.organization_id = organization_id
    self.user_id = user_id
    self.email = email
    self.password = password
    self.development = development

  def __getattr__(self, name):
    return getattr(self.conn, name)


class _TestObservationsCreateHandler(CreatesObservationsMixin, ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = WRITE


class V1Base(BaseTest):
  # pylint: disable=too-many-public-methods
  @pytest.fixture(autouse=True)
  def setup(self, services):
    # pylint: disable=attribute-defined-outside-init
    self.services = services
    # pylint: enable=attribute-defined-outside-init

  small_experiment_meta = {
    "name": "small experiment",
    "type": "offline",
    "parameters": [
      {"name": "x", "type": "double", "bounds": {"min": -2.9, "max": 2.0}},
      {"name": "y", "type": "double", "bounds": {"min": 0.2, "max": 5.1}},
    ],
  }

  offline_experiment_meta = {
    "name": "experiment",
    "type": "offline",
    "parameters": [
      {"name": "a", "type": "double", "bounds": {"min": -2.9, "max": 2.0}},
      {"name": "b", "type": "double", "bounds": {"min": 0.2, "max": 5.1}},
      {"name": "c", "type": "double", "bounds": {"min": 1.2, "max": 15.1}},
      {"name": "x", "type": "double", "bounds": {"min": -2.9, "max": 2.0}},
      {"name": "y", "type": "double", "bounds": {"min": 0.2, "max": 5.1}},
      {"name": "z", "type": "double", "bounds": {"min": 1.2, "max": 15.1}},
    ],
  }

  offline_categorical_experiment_meta = {
    "name": "categorical experiment",
    "type": "offline",
    "parameters": [
      {"name": "x", "type": "double", "bounds": {"min": -2.9, "max": 2.0}},
      {"name": "y", "type": "double", "bounds": {"min": 0.2, "max": 5.1}},
      {"name": "c", "type": "categorical", "categorical_values": [{"name": "a"}, {"name": "b"}, {"name": "c"}]},
    ],
  }

  offline_multimetric_experiment_meta = copy.deepcopy(small_experiment_meta)
  offline_multimetric_experiment_meta["metrics"] = [dict(name="metric1"), dict(name="metric2")]
  offline_multimetric_experiment_meta["observation_budget"] = 100

  offline_named_metric_experiment_meta = copy.deepcopy(small_experiment_meta)
  offline_named_metric_experiment_meta["metrics"] = [dict(name="metric")]

  offline_multitask_experiment_meta = copy.deepcopy(small_experiment_meta)
  offline_multitask_experiment_meta["observation_budget"] = 60
  offline_multitask_experiment_meta["tasks"] = [
    {"name": "cheapest", "cost": 0.1},
    {"name": "cheaper", "cost": 0.3},
    {"name": "expensive", "cost": 1.0},
  ]

  @classmethod
  @pytest.fixture(scope="function")
  def anonymous_connection(cls, config_broker, api):
    api_url = cls.get_api_url(config_broker)
    conn = Connection(
      IntegrationTestConnection(
        api_url=api_url,
        user_token=None,
        client_token="_",
      ),
      client_id=None,
      organization_id=None,
      user_id=None,
    )
    conn.set_client_token("")
    return conn

  @classmethod
  @pytest.fixture(scope="function")
  def connection(cls, config_broker, api, auth_provider):
    return cls.make_v1_connection(config_broker, api, auth_provider, membership=MembershipType.member)

  @classmethod
  @pytest.fixture(scope="function")
  def owner_connection(cls, config_broker, api, auth_provider):
    return cls.make_v1_connection(config_broker, api, auth_provider, membership=MembershipType.owner)

  @classmethod
  @pytest.fixture(scope="function")
  def owner_connection_same_organization(cls, config_broker, api, auth_provider, connection):
    return cls._make_same_client_connection(
      config_broker,
      api,
      auth_provider,
      connection,
      membership_type=MembershipType.owner,
      permission=None,
    )

  @classmethod
  @pytest.fixture(scope="function")
  def admin_connection_same_client(cls, config_broker, api, auth_provider, connection):
    return cls._make_same_client_connection(config_broker, api, auth_provider, connection, permission=ADMIN)

  @classmethod
  @pytest.fixture(scope="function")
  def read_connection(cls, config_broker, api, auth_provider):
    return cls.make_v1_connection(config_broker, api, auth_provider, permission=READ)

  @classmethod
  @pytest.fixture
  def project(cls, connection):
    project_id = random_string(str_length=20).lower()
    return connection.clients(connection.client_id).projects().create(name=project_id, id=project_id)

  @classmethod
  @pytest.fixture
  def another_project(cls, connection):
    project_id = random_string(str_length=20).lower()
    return connection.clients(connection.client_id).projects().create(name=project_id, id=project_id)

  @classmethod
  @pytest.fixture
  def aiexperiment_in_project(cls, connection, project):
    return (
      connection.clients(project.client)
      .projects(project.id)
      .aiexperiments()
      .create(
        name="Test AI Experiment",
        metrics=[dict(name="Accuracy", objective="maximize", strategy="optimize")],
        parameters=[
          {"name": "x", "type": "double", "bounds": {"min": 0, "max": 10}},
          {"name": "y", "type": "int", "bounds": {"min": -0, "max": 10}},
        ],
      )
    )

  @classmethod
  @pytest.fixture(scope="function")
  def read_connection_same_client(cls, config_broker, api, auth_provider, connection):
    return cls._make_same_client_connection(config_broker, api, auth_provider, connection, permission=READ)

  @classmethod
  @pytest.fixture(scope="function")
  def write_connection(cls, config_broker, api, auth_provider):
    return cls.make_v1_connection(config_broker, api, auth_provider, permission=WRITE)

  @classmethod
  @pytest.fixture(scope="function")
  def write_connection_same_client(cls, config_broker, api, auth_provider, connection):
    return cls._make_same_client_connection(config_broker, api, auth_provider, connection, permission=WRITE)

  @classmethod
  @pytest.fixture(scope="function")
  def new_organization_owned_by_connection_user(cls, services, connection):
    user = services.user_service.find_by_id(connection.user_id)
    organization_name = "Test Organization"
    (organization, _) = services.organization_service.set_up_new_organization(
      organization_name=organization_name,
      client_name=organization_name,
      user=user,
      allow_users_to_see_experiments_by_others=True,
      requestor=user,
      user_is_owner=True,
    )
    return organization

  @classmethod
  def make_v1_connection(
    cls,
    config_broker,
    api,
    auth_provider,
    email=None,
    permission=ADMIN,
    membership=MembershipType.member,
    organization_id=None,
    development=False,
    has_verified_email=True,
  ):
    # pylint: disable=too-many-locals
    api_url = cls.get_api_url(config_broker)
    email = email or AuthProvider.randomly_generated_email()
    password = AuthProvider.randomly_generated_password()
    user_id, user_token = auth_provider.create_user_tokens(
      email,
      password,
      has_verified_email=has_verified_email,
    )
    client_id, client_token, organization_id = auth_provider.create_client_tokens(
      user_id=user_id,
      permission=permission,
      membership_type=membership,
      development=development,
    )
    return Connection(
      IntegrationTestConnection(
        api_url=api_url,
        user_token=user_token,
        client_token=client_token,
        development=development,
      ),
      client_id=client_id,
      organization_id=organization_id,
      user_id=user_id,
      email=email,
      password=password,
      development=development,
    )

  @classmethod
  def _make_same_client_connection(
    cls,
    config_broker,
    api,
    auth_provider,
    connection,
    permission,
    client_id=None,
    organization_id=None,
    membership_type=MembershipType.member,
  ):
    if config_broker.get("features.requireInvite"):
      pytest.skip()
    client_id = client_id or connection.client_id
    organization_id = organization_id or connection.organization_id
    api_url = cls.get_api_url(config_broker)
    user_id, user_token = auth_provider.create_user_tokens(has_verified_email=True)
    client_conn = Connection(
      IntegrationTestConnection(
        api_url=api_url,
        user_token=user_token,
      ),
      client_id=client_id,
      organization_id=organization_id,
      user_id=user_id,
    )
    user = client_conn.users(client_conn.user_id).fetch()
    auth_provider.create_membership(user_id=user.id, organization_id=organization_id, membership_type=membership_type)
    if permission:
      auth_provider.create_permission(user_id=user.id, client_id=client_id, permission=permission)
    return client_conn

  @classmethod
  @pytest.fixture(scope="function")
  def development_connection(cls, connection, config_broker, api):
    api_url = cls.get_api_url(config_broker)
    development_token = find(connection.clients(connection.client_id).tokens().fetch().data, lambda t: t.development)
    return Connection(
      IntegrationTestConnection(
        api_url,
        client_token=development_token.token,
      ),
      client_id=connection.client_id,
      organization_id=connection.organization_id,
      development=True,
    )

  @classmethod
  def make_development_connection(cls, config_broker, api, auth_provider):
    return cls.make_v1_connection(config_broker, api, auth_provider, development=True)

  @classmethod
  @pytest.fixture(scope="function")
  def logged_out_connection(cls, config_broker, api):
    return cls.make_logged_out_connection(config_broker, api)

  @classmethod
  def make_logged_out_connection(cls, config_broker, api):
    api_url = cls.get_api_url(config_broker)
    return Connection(
      IntegrationTestConnection(
        api_url=api_url,
        user_token=None,
        client_token=None,
      ),
      client_id=None,
      organization_id=None,
    )

  @classmethod
  @pytest.fixture(scope="function")
  def admin_connection(cls, config_broker, api, auth_provider):
    return cls.make_admin_connection(config_broker, api, auth_provider)

  @classmethod
  def make_admin_connection(cls, config_broker, api, auth_provider):
    api_url = cls.get_api_url(config_broker)
    return Connection(
      IntegrationTestConnection(
        api_url=api_url,
        user_token=auth_provider.create_user_token(),
        client_token=auth_provider.create_user_client_token(),
      ),
      client_id=auth_provider.get_admin_client_id(),
      organization_id=auth_provider.get_admin_organization_id(),
      user_id=auth_provider.get_admin_user_id(),
      email=auth_provider.get_admin_email(),
    )

  @classmethod
  def make_v1_guest_connection(cls, config_broker, api, guest_token=None):
    api_url = cls.get_api_url(config_broker)
    return Connection(
      IntegrationTestConnection(api_url=api_url, user_token=None, client_token=guest_token),
      client_id=None,
      organization_id=None,
    )

  @classmethod
  @pytest.fixture(scope="function")
  def client_only_connection(cls, config_broker, api, auth_provider):
    return cls.make_v1_client_only_connection(config_broker, api, auth_provider)

  @classmethod
  def make_v1_client_only_connection(cls, config_broker, api, auth_provider):
    api_url = cls.get_api_url(config_broker)
    client_id, client_token, organization_id = auth_provider.create_client_tokens()
    return Connection(
      IntegrationTestConnection(
        api_url=api_url,
        client_token=client_token,
      ),
      client_id,
      organization_id,
    )

  @classmethod
  def email_needs_verify(cls, config_broker):
    return config_broker.get("email.verify", True)

  @classmethod
  def verify_email(cls, invitee, invitee_connection, inbox, config_broker):
    code = cls.get_email_verify_code(invitee, invitee_connection, inbox)
    return cls.do_verify_email(config_broker, code, invitee.email, invitee_connection)

  @classmethod
  def get_email_verify_code(cls, invitee, invitee_connection, inbox):
    invitee_connection.verifications().create(email=invitee.email)
    return extract_verify_code(inbox, invitee.email)

  @classmethod
  def do_verify_email(cls, config_broker, code, email, connection):
    return connection.sessions().create(email=email, code=code)

  def batch_upload_observations(self, experiment, observations, no_optimize=True):
    ret = []
    experiment = self.services.database_service.first(
      self.services.database_service.query(Experiment).filter_by(id=experiment.id)
    )
    for o in observations:
      validate_observation_json_dict_for_create(o, experiment)
      obs = Observation(experiment_id=experiment.id)
      observation_data = ObservationData()
      handler = _TestObservationsCreateHandler(self.services, req=None, experiment_id=experiment.id)
      handler.experiment = experiment
      handler.observation_from_json(
        o,
        timestamp=datetime_to_seconds(current_datetime()),
        observation=obs,
        observation_data=observation_data,
      )
      obs.data = observation_data
      ret.append(obs)
    self.services.database_service.insert_all(ret)
    if not no_optimize:
      self.services.optimizer.trigger_hyperparameter_optimization(experiment)
      self.services.optimizer.trigger_next_points(experiment)
