# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# pylint: disable=too-many-lines
from http import HTTPStatus

import pytest

from zigopt.common import *
from zigopt.common.sigopt_datetime import unix_timestamp
from zigopt.common.strings import random_string
from zigopt.invite.constant import ADMIN_ROLE, NO_ROLE, READ_ONLY_ROLE
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, READ, WRITE, TokenMeta
from zigopt.token.model import Token
from zigopt.token.token_types import TokenType

from integration.auth import AuthProvider
from integration.base import RaisesApiException
from integration.connection import IntegrationTestConnection
from integration.utils.random_assignment import random_assignments
from integration.v1.constants import DEFAULT_AI_EXPERIMENT_META
from integration.v1.test_base import Connection, V1Base


class TestAuth(V1Base):
  @classmethod
  @pytest.fixture(scope="function")
  def client_id(cls, connection):
    return connection.client_id

  @classmethod
  @pytest.fixture(scope="function", params=["api", "dev"])
  def any_attacker(cls, config_broker, api, auth_provider, request, attacker, dev_attacker):
    del dev_attacker
    return cls.make_v1_connection(config_broker, api, auth_provider, development=(request.param == "dev"))

  @classmethod
  @pytest.fixture(scope="function")
  def attacker(cls, config_broker, api, auth_provider, request):
    return cls.make_v1_connection(config_broker, api, auth_provider, development=False)

  @classmethod
  @pytest.fixture(scope="function")
  def dev_attacker(cls, config_broker, api, auth_provider, request):
    return cls.make_v1_connection(config_broker, api, auth_provider, development=True)

  @classmethod
  @pytest.fixture(scope="function")
  def other_attacker(cls, config_broker, api, auth_provider):
    return cls.make_v1_connection(config_broker, api, auth_provider)

  @classmethod
  @pytest.fixture(scope="function")
  def logged_out(cls, config_broker, api):
    return cls.make_logged_out_connection(config_broker, api)

  @classmethod
  @pytest.fixture(scope="function")
  def other_user(cls, config_broker, api, auth_provider):
    return cls.make_v1_connection(config_broker, api, auth_provider)

  @classmethod
  @pytest.fixture(scope="function")
  def invitee_connection(cls, config_broker, api, auth_provider, api_url):
    return cls.make_v1_connection(config_broker, api, auth_provider, has_verified_email=False)

  @pytest.fixture
  def invitee(self, connection, invitee_connection, client_id):
    invitee = invitee_connection.connection.sessions().fetch().user
    connection.clients(client_id).invites().create(email=invitee.email, role=READ_ONLY_ROLE, old_role=NO_ROLE)
    return invitee

  def test_user(self, connection, attacker):
    user_id = connection.user_id

    connection.users(user_id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.users(user_id).fetch()

    connection.users(user_id).experiments().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.users(user_id).experiments().fetch()

    connection.users(user_id).update(name="new name")
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.users(user_id).update(name="new name")

  def test_can_see_user(
    self,
    connection,
    services,
    client_id,
    other_user,
    invitee,
    inbox,
    config_broker,
    anonymous_connection,
  ):
    # invitee needs email verified to be added to the same client
    self.verify_email(invitee, anonymous_connection, inbox, config_broker)

    # READ permissions required
    # Fetching oneself
    assert connection.user_id == connection.users(connection.user_id).fetch().id
    # Can't fetch a user from a diferent client
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.users(other_user.user_id).fetch()
    # Can fetch a user from the same client
    assert invitee.id == connection.users(invitee.id).fetch().id

    # WRITE permissions required
    # Updating oneself
    connection.users(connection.user_id).update(name="new name")
    assert connection.users(connection.user_id).fetch().name == "new name"
    # Can't see user from a different client
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.users(other_user.user_id).fetch()
    # Can't update user from a different client
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.users(other_user.user_id).update(name="new name")
    user = services.user_service.find_by_id(other_user.user_id)
    assert user.name != "new name"
    # Can see user from the same client
    connection.users(invitee.id).fetch()
    # Can't update user from the same client
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.users(invitee.id).update(name="new name")
    user = services.user_service.find_by_id(invitee.id)
    assert user.name != "new name"

  def test_user_delete_no_password(self, connection, attacker, config_broker):
    # With no password, 404 error so that we don't leak whether or not the user exists.
    # Required params are checked after we ensure that the caller has
    # permissions to view the user.
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.users(connection.user_id).delete()

  def test_user_delete_wrong_password(self, connection, attacker, config_broker):
    # With wrong password, 404 error so that we don't leak whether
    # or not the user exists
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.users(connection.user_id).delete(password="wrong password")

  def test_user_delete_right_password(self, connection, attacker, config_broker):
    # Even if the attacker knows the user's password, we should still 404 when you try
    # to delete someone else, just to prevent accidents. This is not really a security
    # measure, since the attacker now knows enough to log in as the user
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.users(connection.user_id).delete(password=connection.password)

  def test_client(self, connection, attacker):
    client_id = connection.client_id
    connection.clients(client_id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).fetch()

    connection.clients(client_id).update(name="Client name")
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).update(name="Client name")

    connection.clients(client_id).experiments().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).experiments().fetch()

    # connection.clients(client_id).delete()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).delete()

  def test_client_project(self, connection, attacker, services):
    client_id = connection.client_id
    project_id = random_string(str_length=20).lower()

    connection.clients(client_id).projects().create(name=random_string(), id=project_id)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).projects().create(name=random_string(), id=random_string())

    connection.clients(client_id).projects(project_id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).projects(project_id).fetch()

    connection.clients(client_id).projects(project_id).experiments().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).projects(project_id).experiments().fetch()

    connection.clients(client_id).projects(project_id).notes().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).projects(project_id).notes().fetch()

    connection.clients(client_id).projects(project_id).notes().create(contents="Ayo boi wassup")
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).projects(project_id).notes().create(contents="Ayo boi wassup")

    connection.clients(client_id).projects(project_id).training_runs().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).projects(project_id).training_runs().fetch()

    connection.clients(client_id).projects(project_id).training_runs().create(name="some name")
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).projects(project_id).training_runs().create(name="some name")

    connection.clients(client_id).projects(project_id).update(name=random_string())
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).projects(project_id).update(name=random_string())

    connection.clients(client_id).projects().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).projects().fetch()

    connection.clients(client_id).tags().create(name="tag name", color="#123123")
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).tags().create(name="tag name", color="#123123")

    connection.clients(client_id).tags().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).tags().fetch()

    run = connection.clients(client_id).projects(project_id).training_runs().create(name="some name")
    file_info = (
      connection.training_runs(run.id)
      .files()
      .create(
        name="file name",
        filename="file.txt",
        content_type="text/plain",
        content_md5="hErGgMwOlw3IRZlwWueI+g==",
        content_length=123,
      )
    )
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.training_runs(run.id).files().create(
        name="file name",
        filename="file.txt",
        content_type="text/plain",
        content_md5="hErGgMwOlw3IRZlwWueI+g==",
        content_length=123,
      )

    connection.files(file_info.id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.files(file_info.id).fetch()

  def test_experiment(self, connection, any_attacker):
    with connection.create_any_experiment() as e:
      update_meta = {"parameters": [pick(p.to_json(), "name") for p in e.parameters]}
      connection.experiments(e.id).fetch()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).fetch()

      connection.experiments(e.id).update(**update_meta)
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).update(**update_meta)

      # Delete occurs automatically at end
      # connection.experiments(e.id).delete()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).delete()

  def test_ai_experiment(self, connection, any_attacker):
    p = connection.clients(connection.client_id).projects().create(id="test-auth-project", name="Test auth project")
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.clients(p.client).projects(p.id).aiexperiments().create()
    aie = connection.clients(p.client).projects(p.id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.aiexperiments(aie.id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.aiexperiments(aie.id).update()
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.aiexperiments(aie.id).delete()
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.aiexperiments(aie.id).training_runs().create()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      any_attacker.clients(p.client).projects(p.id).aiexperiments().fetch()

  def test_development_token(self, connection, development_connection):
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      development_connection.users(connection.user_id).fetch()

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      development_connection.users(connection.user_id).update()

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      development_connection.clients(connection.client_id).update()

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      development_connection.clients(connection.client_id).tokens().fetch()

    with connection.create_any_experiment() as experiment:
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        development_connection.experiments(experiment.id).fetch()

    with development_connection.create_any_experiment() as development_experiment:
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        connection.as_client_only().experiments(development_experiment.id).fetch()

  def test_client_read_write(self, read_connection, write_connection):
    # Read, writes can't update client
    read_connection.clients(read_connection.client_id).fetch()
    write_connection.clients(write_connection.client_id).fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      read_connection.clients(read_connection.client_id).update(name="new name")
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      write_connection.clients(write_connection.client_id).update(name="new name")
    # Read, writes can't delete client
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      read_connection.clients(read_connection.client_id).delete()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      write_connection.clients(write_connection.client_id).delete()

    read_connection.clients(read_connection.client_id).permissions().fetch()
    write_connection.clients(write_connection.client_id).permissions().fetch()

    read_connection.clients(read_connection.client_id).tokens().fetch()
    write_connection.clients(write_connection.client_id).tokens().fetch()

  def test_experiment_read_write(self, read_connection_same_client, write_connection_same_client):
    read_connection = read_connection_same_client
    write_connection = write_connection_same_client
    with write_connection.create_experiment_as(read_connection.client_id) as e:
      assert e.client == read_connection.client_id
      read_connection.experiments(e.id).fetch()
      # Read can't create guest tokens
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).tokens().create()
      # Read cannot alter experiments
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).update(name="new name")
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).delete()
      # Read cannot create experiments
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.create_any_experiment()

    with write_connection.create_experiment_as(write_connection.client_id) as e:
      assert e.client == write_connection.client_id
      write_connection.experiments(e.id).fetch()
      write_connection.experiments(e.id).tokens().create()

  @pytest.fixture(params=["production", "development"])
  def guest_token_connection(self, request, connection, development_connection):
    if request.param == "production":
      return connection
    assert request.param == "development"
    return development_connection

  @pytest.fixture
  @unsafe_generator
  def guest_experiment(self, request, connection):
    with connection.create_any_experiment() as e:
      yield e

  def _make_experiment_guest_connection(self, connection, experiment, api, config_broker):
    token = connection.experiments(experiment.id).tokens().create()
    assert token.experiment == experiment.id
    assert token.development == connection.development
    return self.make_v1_guest_connection(config_broker, api, token.token)

  @pytest.fixture
  def guest_with_experiment(self, request, connection, api, guest_experiment, config_broker):
    return self._make_experiment_guest_connection(connection, guest_experiment, api, config_broker)

  @pytest.fixture(params=["experiment", "training_run"])
  def any_guest(self, request, connection, api, config_broker):
    if request.param == "experiment":
      with connection.create_any_experiment() as e:
        yield self._make_experiment_guest_connection(connection, e, api, config_broker)
    else:
      assert request.param == "training_run"
      project_id = random_string(str_length=20).lower()
      connection.clients(connection.client_id).projects().create(name=project_id, id=project_id)
      training_run = connection.clients(connection.client_id).projects(project_id).training_runs().create(name="run")
      token = connection.training_runs(training_run.id).tokens().create()
      assert token.training_run == training_run.id
      assert token.experiment is None
      assert token.development == connection.development
      yield self.make_v1_guest_connection(config_broker, api, token.token)

  def test_experiment_guest_token_dev(self, development_connection, attacker, config_broker):
    with development_connection.create_any_experiment() as e:
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        development_connection.experiments(e.id).tokens().create()

  @pytest.mark.slow
  def test_experiment_guest_token(self, connection, guest_with_experiment, guest_experiment, attacker):
    # pylint: disable=too-many-statements
    # Guests cant reshare experiments
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).tokens().create()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.experiments(guest_experiment.id).tokens().create()

    # Guests are allowed to view the experiment their token is for
    connection.experiments(guest_experiment.id).fetch()
    guest_with_experiment.experiments(guest_experiment.id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.experiments(guest_experiment.id).fetch()

    # Guests cannot call the experiments endpoint
    connection.create_any_experiment()
    conn_experiments = connection.clients(connection.client_id).experiments().fetch()
    assert len(conn_experiments.data) == 2
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.clients(connection.client_id).experiments().fetch()

    # Guests can't modify the experiment their token is for
    update_meta = {"parameters": [pick(p.to_json(), "name") for p in guest_experiment.parameters]}
    connection.experiments(guest_experiment.id).update(**update_meta)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.experiments(guest_experiment.id).update(**update_meta)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).update(**update_meta)

    # Guests can't delete
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.experiments(guest_experiment.id).delete()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).delete()
    # guest_token_connection.experiments(guest_experiment.id).delete()  # Occurs automatically at end

    # Guests can't create suggestions
    suggestion = connection.experiments(guest_experiment.id).suggestions().create()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).suggestions().create()
    guest_with_experiment.experiments(guest_experiment.id).suggestions(suggestion.id).fetch()
    guest_with_experiment.experiments(guest_experiment.id).suggestions().fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).suggestions(suggestion.id).delete()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).suggestions().delete()

    # Guests can't create observations
    observation_data = {"assignments": random_assignments(guest_experiment), "values": [{"value": 10}]}
    observation = connection.experiments(guest_experiment.id).observations().create(**observation_data)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).observations().create(**observation_data)
    guest_with_experiment.experiments(guest_experiment.id).observations(observation.id).fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).observations(observation.id).update(**observation_data)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).observations(observation.id).delete()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      guest_with_experiment.experiments(guest_experiment.id).observations().delete()

    # Guests cannot view other experiments from the host client
    with connection.create_any_experiment() as e_2:
      connection.experiments(e_2.id).fetch()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        attacker.experiments(e_2.id).fetch()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        guest_with_experiment.experiments(e_2.id).fetch()

    # Guests also cannot view any experiments from other clients
    with attacker.create_any_experiment() as attacker_e:
      attacker.experiments(attacker_e.id).fetch()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        connection.experiments(attacker_e.id).fetch()

    # Guests also cannot view any experiments from other clients
    with attacker.create_any_experiment() as attacker_e:
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        guest_with_experiment.experiments(attacker_e.id).fetch()

  def test_client_guest_token(self, connection, any_guest, attacker):
    # Guests cannot access non-experiment endpoints
    connection.clients(connection.client_id).fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      any_guest.clients(connection.client_id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(connection.client_id).fetch()

    # Guests can't update, delete client
    connection.clients(connection.client_id).update(name="new name")
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      any_guest.clients(connection.client_id).update(name="new name")
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      any_guest.clients(connection.client_id).delete()

    # Guests can't see/modify other tokens
    client_token = any_guest.client_token
    connection.tokens(client_token).fetch()
    any_guest.tokens(client_token).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.tokens(client_token).fetch()

    # Guests can't view client permissions
    connection.clients(connection.client_id).permissions().fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      any_guest.clients(connection.client_id).permissions().fetch()

  def test_user_guest_token(self, connection, any_guest, services):
    # any_guest can't fetch, update user
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      any_guest.users(connection.user_id).fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      any_guest.users(connection.user_id).update(name="new name")
    user = services.user_service.find_by_id(connection.user_id)
    assert user.name != "new name"

  def test_experiment_modify_token(self, connection, any_guest, attacker):
    client_token = any_guest.client_token

    client_id = connection.client_id
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).tokens().fetch()
    connection.clients(client_id).tokens().fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      any_guest.clients(client_id).tokens().fetch()

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.tokens(connection.client_token).fetch()
    connection.tokens(connection.client_token).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      any_guest.tokens(connection.client_token).fetch()

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.tokens(connection.client_token).delete()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      any_guest.tokens(connection.client_token).delete()

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.tokens(client_token).delete()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      any_guest.tokens(client_token).delete()
    connection.tokens(client_token).delete()

  def test_suggestion(self, connection, any_attacker):
    with connection.create_any_experiment() as e:
      suggestion = connection.experiments(e.id).suggestions().create()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).suggestions().create()

      connection.experiments(e.id).suggestions(suggestion.id).fetch()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).suggestions(suggestion.id).fetch()

      connection.experiments(e.id).suggestions().fetch()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).suggestions().fetch()

      connection.experiments(e.id).suggestions(suggestion.id).delete()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).suggestions(suggestion.id).delete()

      connection.experiments(e.id).suggestions().delete()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).suggestions().delete()

  def test_observation(self, connection, any_attacker):
    experiment_meta = {
      "type": "offline",
      "parameters": [
        {"name": "a", "type": "int", "bounds": {"min": 1, "max": 50}},
      ],
    }
    observation_data = {
      "assignments": {
        "a": 5,
      },
      "values": [{"value": 10}],
    }
    with connection.create_experiment(experiment_meta) as e:
      observation = connection.experiments(e.id).observations().create(**observation_data)
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).observations().create(**observation_data)

      connection.experiments(e.id).observations(observation.id).fetch()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).observations(observation.id).fetch()

      connection.experiments(e.id).observations(observation.id).update(**observation_data)
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).observations(observation.id).update(**observation_data)

      connection.experiments(e.id).observations(observation.id).delete()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).observations(observation.id).delete()

      connection.experiments(e.id).observations().delete()
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        any_attacker.experiments(e.id).observations().delete()

  def test_read_observation_suggestion(self, write_connection_same_client, read_connection_same_client):
    read_connection = read_connection_same_client
    write_connection = write_connection_same_client

    with write_connection.create_experiment_as(read_connection.client_id) as e:
      assert e.client == read_connection.client_id
      read_connection.experiments(e.id).fetch()

      suggestion = write_connection.experiments(e.id).suggestions().create()

      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).suggestions().create()
      read_connection.experiments(e.id).suggestions(suggestion.id).fetch()
      read_connection.experiments(e.id).suggestions().fetch()
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).suggestions(suggestion.id).delete()
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).suggestions().delete()

      observation = (
        write_connection.experiments(e.id).observations().create(suggestion=suggestion.id, values=[{"value": 1}])
      )

      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).observations().create(suggestion=suggestion.id, values=[{"value": 1}])
      read_connection.experiments(e.id).observations(observation.id).fetch()
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).observations(observation.id).update(values=[{"value": 1}])
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).observations(observation.id).delete()
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        read_connection.experiments(e.id).observations().delete()

  def test_training_run_attacker(self, connection, any_attacker):
    client_id = connection.client_id
    project_id = random_string(str_length=20).lower()
    connection.clients(client_id).projects().create(name=random_string(), id=project_id)

    connection.clients(client_id).projects(project_id).training_runs().create(name="run")
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.clients(client_id).projects(project_id).training_runs().create(name="run")

    e = connection.clients(client_id).projects(project_id).aiexperiments().create(**DEFAULT_AI_EXPERIMENT_META)

    training_run = connection.aiexperiments(e.id).training_runs().create(name="test")
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.aiexperiments(e.id).training_runs().create(name="test")

    connection.training_runs(training_run.id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      any_attacker.training_runs(training_run.id).fetch()

    connection.training_runs(training_run.id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.training_runs(training_run.id).fetch()

    connection.training_runs(training_run.id).update(name="abc")
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.training_runs(training_run.id).update(name="abc")

    connection.training_runs(training_run.id).checkpoints().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.training_runs(training_run.id).checkpoints().fetch()

    values = [{"name": "metric", "value": 1.0}]
    checkpoint = connection.training_runs(training_run.id).checkpoints().create(values=values)
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.training_runs(training_run.id).checkpoints().create(values=values)

    connection.training_runs(training_run.id).checkpoints(checkpoint.id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.training_runs(training_run.id).checkpoints(checkpoint.id).fetch()

    with RaisesApiException(HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN):
      any_attacker.training_runs(training_run.id).delete()
    connection.training_runs(training_run.id).delete()

  def test_checkpoints(self, connection, any_attacker):
    client_id = connection.client_id
    project_id = random_string(str_length=20).lower()
    connection.clients(client_id).projects().create(name=random_string(), id=project_id)
    tr = connection.clients(client_id).projects(project_id).training_runs().create(name="test checkpoints")

    attacker_client_id = any_attacker.client_id
    attacker_project_id = random_string(str_length=20).lower()
    any_attacker.clients(attacker_client_id).projects().create(name=random_string(), id=attacker_project_id)
    attacker_tr = (
      any_attacker.clients(attacker_client_id)
      .projects(attacker_project_id)
      .training_runs()
      .create(name="test checkpoints attacker")
    )

    checkpoint = connection.training_runs(tr.id).checkpoints().create(values=[{"name": "metric", "value": 2}])
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      any_attacker.training_runs(tr.id).checkpoints().create(values=[{"name": "metric", "value": 2}])

    connection.training_runs(tr.id).checkpoints(checkpoint.id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      any_attacker.training_runs(tr.id).checkpoints(checkpoint.id).fetch()

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      any_attacker.training_runs(attacker_tr.id).checkpoints(checkpoint.id).fetch()

  def test_training_run_checkpoint_read(self, write_connection_same_client, read_connection_same_client):
    client_id = write_connection_same_client.client_id
    project_id = random_string(str_length=20).lower()
    write_connection_same_client.clients(client_id).projects().create(name=random_string(), id=project_id)
    read_connection_same_client.clients(client_id).projects(project_id).fetch()

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      read_connection_same_client.clients(client_id).projects(project_id).training_runs().create(
        name="test read checkpoints"
      )

    training_run = (
      write_connection_same_client.clients(client_id)
      .projects(project_id)
      .training_runs()
      .create(name="test read checkpoints")
    )
    assert read_connection_same_client.clients(client_id).projects(project_id).training_runs().fetch().count == 1

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      read_connection_same_client.training_runs(training_run.id).checkpoints().create(
        values=[{"name": "metric", "value": 5}]
      )

    checkpoint = (
      write_connection_same_client.training_runs(training_run.id)
      .checkpoints()
      .create(values=[{"name": "metric", "value": 5}])
    )
    read_connection_same_client.training_runs(training_run.id).checkpoints(checkpoint.id).fetch()

  def test_user_create(self, connection, attacker):
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.clients(connection.client_id).users().create(
        **{"email": "foo@bar.com", "name": "foo bar", "password": "foobar"}
      )

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(attacker.client_id).users().create(
        **{"email": "foo@bar.com", "name": "foo bar", "password": "foobar"}
      )

  def test_permissions_and_pending_permissions(self, connection, attacker):
    user_id = connection.user_id
    client_id = connection.client_id

    connection.users(user_id).permissions().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.users(user_id).permissions().fetch()

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.users(user_id).permissions().create()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.users(user_id).permissions().create()

    connection.clients(client_id).permissions().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).permissions().fetch()

    connection.clients(client_id).pending_permissions().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(client_id).pending_permissions().fetch()

  def attempt_adversarial_client_invites(self, connection, attacker, other_attacker):
    user_email = connection.sessions().fetch().user.email
    attacker_email = attacker.sessions().fetch().user.email
    other_attacker_email = other_attacker.sessions().fetch().user.email
    assert attacker_email != user_email
    assert attacker_email != other_attacker_email
    assert attacker.client_id != connection.client_id

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(connection.client_id).invites().create(email=user_email, role=READ_ONLY_ROLE, old_role=NO_ROLE)

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(connection.client_id).invites().create(
        email=attacker_email, role=READ_ONLY_ROLE, old_role=NO_ROLE
      )

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.clients(connection.client_id).invites().create(
        email=other_attacker_email, role=READ_ONLY_ROLE, old_role=NO_ROLE
      )

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      other_attacker.clients(connection.client_id).invites().create(
        email=attacker_email, role=READ_ONLY_ROLE, old_role=NO_ROLE
      )

  def attempt_adversarial_organization_invites(self, connection, attacker, other_attacker):
    user_email = connection.sessions().fetch().user.email
    attacker_email = attacker.sessions().fetch().user.email
    other_attacker_email = other_attacker.sessions().fetch().user.email
    assert attacker_email != user_email
    assert attacker_email != other_attacker_email
    assert attacker.organization_id != connection.organization_id

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.organizations(connection.organization_id).invites().create(
        email=user_email,
        client_invites=[],
        membership_type="owner",
      )

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.organizations(connection.organization_id).invites().create(
        email=attacker_email,
        client_invites=[],
        membership_type="owner",
      )

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.organizations(connection.organization_id).invites().create(
        email=other_attacker_email,
        client_invites=[],
        membership_type="owner",
      )

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      other_attacker.organizations(connection.organization_id).invites().create(
        email=attacker_email,
        client_invites=[],
        membership_type="owner",
      )

  def test_invite(self, connection, attacker, other_attacker):
    # Make sure outsiders can't invite themselves or others
    self.attempt_adversarial_client_invites(connection, attacker, other_attacker)
    self.attempt_adversarial_organization_invites(connection, attacker, other_attacker)

  def test_invite_after_invited(self, connection, other_attacker, config_broker, api, auth_provider):
    # Outsiders can't invite if they have been invited but not verified
    if config_broker.get("email.verify") is False:
      pytest.skip()
    attacker_email = AuthProvider.randomly_generated_email()
    unverified_attacker = self.make_v1_connection(
      config_broker,
      api,
      auth_provider,
      email=attacker_email,
      has_verified_email=False,
    )
    connection.clients(connection.client_id).invites().create(
      email=attacker_email, role=READ_ONLY_ROLE, old_role=NO_ROLE
    )
    self.attempt_adversarial_client_invites(connection, unverified_attacker, other_attacker)
    self.attempt_adversarial_organization_invites(connection, unverified_attacker, other_attacker)

  def test_invite_after_uninvited(self, connection, attacker, other_attacker):
    # Outsiders can't invite if they have been invited and then uninvited
    attacker_email = attacker.sessions().fetch().user.email
    connection.clients(connection.client_id).invites().create(
      email=attacker_email, role=READ_ONLY_ROLE, old_role=NO_ROLE
    )
    connection.clients(connection.client_id).invites().delete(email=attacker_email)
    self.attempt_adversarial_client_invites(connection, attacker, other_attacker)
    self.attempt_adversarial_organization_invites(connection, attacker, other_attacker)

  def test_sessions(self, connection, attacker):
    user_session = connection.sessions().fetch()
    attacker_session = attacker.sessions().fetch()

    user_id = user_session.user.id
    user_email = user_session.user.email
    user_token = user_session.api_token.token
    assert user_id != attacker_session.user.id
    assert user_email != attacker_session.user.email
    assert user_token != attacker_session.api_token.token

    # Can't see someone else's session
    assert attacker.sessions().fetch(email=user_email).api_token.token != user_token

    # Can't create a session as someone else without their credentials
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      attacker.sessions().create(email=user_email, code="wrong code")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      attacker.sessions().create(email=user_email, password="wrong password")
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      attacker.sessions().create(email=user_email)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      attacker.sessions().create(email=user_email, password="wrong password", code="wrong code")
    connection.sessions().create(email=user_email, password=connection.password)

    # No one can see user's sessions
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      connection.users(user_id).sessions().fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.users(user_id).sessions().fetch()

  def test_session_prefs(self, owner_connection, write_connection, api_url, api):
    def check_session(connection, prefer, expect):
      fetched_session = connection.sessions().fetch(preferred_client_id=prefer)
      assert fetched_session.client.id == expect

    owner_session = owner_connection.sessions().fetch()
    client_1 = owner_session.client.id
    client_2 = owner_connection.clients().create(name="Non-preferred client").id
    assert len({client_1, client_2}) == 2

    assert owner_connection.client_id != write_connection.client_id
    assert client_1 != client_2

    check_session(owner_connection, prefer=client_1, expect=client_1)
    check_session(owner_connection, prefer=client_2, expect=client_2)
    check_session(owner_connection, prefer="99999999999", expect=client_1)

    check_session(write_connection, prefer=client_2, expect=write_connection.client_id)

    # Ensure that a token that has an associated client id can't swap client ids
    all_tokens = list(owner_connection.clients(owner_connection.client_id).tokens().fetch().iterate_pages())
    client_token = find(all_tokens, lambda t: t.user == owner_connection.user_id and not t.development)
    client_connection = Connection(
      IntegrationTestConnection(api_url, api, client_token.token),
      email=owner_connection.email,
      password=owner_connection.password,
      client_id=client_token.client,
      organization_id=None,
    )
    check_session(client_connection, prefer=client_1, expect=client_1)
    check_session(client_connection, prefer=client_2, expect=client_1)

  def test_client_session(self, connection):
    # Endpoint works with a client token
    user_session = connection.sessions().fetch()
    client_session = connection.as_client_only().sessions().fetch()
    assert client_session.api_token is not None
    assert client_session.api_token != user_session.api_token
    assert client_session.user == user_session.user
    assert client_session.client == user_session.client

  def test_organization_owner(self, owner_connection, config_broker):
    organization_id = owner_connection.organization_id

    owner_connection.organizations(organization_id).fetch()

    owner_connection.organizations(organization_id).update(name="New Name")

    owner_connection.organizations(organization_id).memberships().fetch()

    owner_connection.organizations(organization_id).clients().fetch()

  def test_organization_member(self, connection, config_broker):
    organization_id = connection.organization_id

    connection.organizations(organization_id).fetch()

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.organizations(organization_id).update(name="New Name")

    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.organizations(organization_id).memberships().fetch()

    connection.organizations(organization_id).clients().fetch()

  def test_organization_attacker(self, connection, attacker):
    organization_id = connection.organization_id

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.organizations(organization_id).fetch()

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.organizations(organization_id).update(name="New Name")

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.organizations(organization_id).memberships().fetch()

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.organizations(organization_id).clients().fetch()

  @pytest.mark.parametrize(
    "endpoint,attr",
    [
      ("users", "user_id"),
      ("organizations", "organization_id"),
      ("clients", "client_id"),
    ],
  )
  def test_error_message_doesnt_reveal_absence(self, connection, attacker, endpoint, attr):
    real_id = getattr(connection, attr)
    fake_id = str(9999999999)

    with RaisesApiException(HTTPStatus.NOT_FOUND) as real_not_found:
      getattr(attacker, endpoint)(real_id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND) as fake_not_found:
      getattr(attacker, endpoint)(fake_id).fetch()
    assert str(real_not_found)[::-1].replace(real_id[::-1], "id-goes-here", 1) == str(fake_not_found)[::-1].replace(
      fake_id[::-1], "id-goes-here", 1
    )

  def test_tags(self, connection, attacker):
    project_id = random_string(str_length=20).lower()
    tag = connection.clients(connection.client_id).tags().create(name="tag name", color="#123123")

    project = connection.clients(connection.client_id).projects().create(name="test tag attacker", id=project_id)
    run = connection.clients(connection.client_id).projects(project.id).training_runs().create(name="test run")

    attacker_project = attacker.clients(attacker.client_id).projects().create(name="test tag attacker", id=project_id)
    attacker_run = (
      attacker.clients(attacker.client_id).projects(attacker_project.id).training_runs().create(name="test run")
    )

    connection.training_runs(run.id).tags().create(id=tag.id)
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.training_runs(run.id).tags().create(id=tag.id)
    with RaisesApiException(HTTPStatus.UNPROCESSABLE_ENTITY):
      attacker.training_runs(attacker_run.id).tags().create(id=tag.id)

    connection.training_runs(run.id).tags(tag.id).delete()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.training_runs(run.id).tags(tag.id).delete()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      attacker.training_runs(attacker_run.id).tags(tag.id).delete()


class TestTokens(V1Base):
  def test_guest_not_expired(self, connection, db_connection, api, api_url):
    now = unix_timestamp()
    with connection.create_any_experiment() as e:
      token = Token(
        token_type=TokenType.GUEST,
        client_id=connection.client_id,
        user_id=None,
        meta=TokenMeta(
          date_created=now,
          guest_experiment_id=int(e.id),
          guest_permissions=READ,
        ),
      )
      db_connection.insert(token)
      new_connection = IntegrationTestConnection(api_url, api, token.token)
      token_obj = new_connection.tokens("self").fetch()
      assert token_obj.token == token.token
      assert token_obj.token_type == "guest"
      assert token_obj.permissions == "read"
      assert token_obj.development is False
      assert token_obj.client == connection.client_id
      assert token_obj.user is None
      assert token_obj.experiment == e.id
      assert token_obj.expires > now
      assert new_connection.experiments(e.id).fetch().id == e.id

  def test_guest_expired(self, connection, db_connection, api, api_url):
    with connection.create_any_experiment() as e:
      token = Token(
        token_type=TokenType.GUEST,
        client_id=connection.client_id,
        user_id=None,
        meta=TokenMeta(
          date_created=1,
          guest_experiment_id=int(e.id),
          guest_permissions=READ,
        ),
      )
      db_connection.insert(token)
      new_connection = IntegrationTestConnection(api_url, api, token.token)
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        new_connection.tokens("self").fetch()
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        new_connection.experiments(e.id).fetch()

  def test_guest_write_not_expired(self, connection, db_connection, api, api_url):
    with connection.create_any_experiment() as e:
      token = Token(
        token_type=TokenType.GUEST,
        client_id=connection.client_id,
        user_id=None,
        meta=TokenMeta(
          date_created=1,
          guest_permissions=WRITE,
        ),
      )
      db_connection.insert(token)
      new_connection = IntegrationTestConnection(api_url, api, token.token)
      token_obj = new_connection.tokens("self").fetch()
      assert token_obj.expires is None
      assert new_connection.experiments(e.id).fetch().id == e.id

  def test_guest_lasts_forever(self, connection, db_connection, api, api_url):
    with connection.create_any_experiment() as e:
      token = Token(
        token_type=TokenType.GUEST,
        client_id=connection.client_id,
        user_id=None,
        meta=TokenMeta(
          date_created=1,
          guest_experiment_id=int(e.id),
          guest_permissions=READ,
          lasts_forever=True,
        ),
      )
      db_connection.insert(token)
      new_connection = IntegrationTestConnection(api_url, api, token.token)
      token_obj = new_connection.tokens("self").fetch()
      assert token_obj.expires is None
      assert new_connection.experiments(e.id).fetch().id == e.id


class TestPermissions(V1Base):
  def invite(self, connection, email, role=ADMIN_ROLE):
    connection.clients(connection.client_id).invites().create(email=email, role=role, old_role=NO_ROLE)

  def ensure_other_connection_cant_see(self, connection, other_connection):
    other_session = other_connection.sessions().fetch()
    assert napply(other_session.client, lambda c: c.id) != connection.client_id
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      other_connection.clients(connection.client_id).fetch()
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      other_connection.clients(connection.client_id).permissions().fetch()
    assert other_session.user.id not in [
      p.user.id for p in connection.clients(connection.client_id).permissions().fetch().iterate_pages()
    ]
    assert connection.client_id not in [
      p.client.id for p in other_connection.users(other_connection.user_id).permissions().fetch().iterate_pages()
    ]

  def test_unverified_invitee_cant_access(self, connection, api, anonymous_connection, config_broker, auth_provider):
    other_email = AuthProvider.randomly_generated_email()
    self.invite(connection, other_email)
    other_connection = self.make_v1_connection(config_broker, api, auth_provider, email=other_email)
    self.ensure_other_connection_cant_see(connection, other_connection)

  def test_inviting_unverified_cant_access(self, connection, api, anonymous_connection, config_broker, auth_provider):
    if config_broker.get("email.verify") is False:
      pytest.skip()
    other_email = AuthProvider.randomly_generated_email()
    other_connection = self.make_v1_connection(
      config_broker,
      api,
      auth_provider,
      email=other_email,
      has_verified_email=False,
    )
    self.invite(connection, other_email)
    self.ensure_other_connection_cant_see(connection, other_connection)

  @pytest.mark.slow
  def test_inviting_new_user_joins(self, connection, anonymous_connection, inbox, config_broker, auth_provider):
    email = AuthProvider.randomly_generated_email()
    self.invite(connection, email)
    password = AuthProvider.randomly_generated_password()
    other_user = auth_provider.create_user(email=email, password=password, has_verified_email=False)
    self.verify_email(other_user, anonymous_connection, inbox, config_broker)

    user_session = connection.sessions().fetch()
    other_session = anonymous_connection.sessions().create(email=email, password=password)
    assert user_session.user.id != other_session.user.id
    assert user_session.api_token.token != other_session.api_token.token
    assert user_session.client.id == other_session.client.id

    assert other_user.id in [
      p.user.id for p in connection.clients(connection.client_id).permissions().fetch().iterate_pages()
    ]

  @pytest.mark.slow
  def test_inviting_existing_user_can_access(self, connection, api, config_broker, auth_provider, inbox):
    other_connection = self.make_v1_connection(config_broker, api, auth_provider)
    other_user = other_connection.users(other_connection.user_id).fetch()
    self.invite(connection, other_user.email)
    assert other_user.id in [
      p.user.id for p in connection.clients(connection.client_id).permissions().fetch().iterate_pages()
    ]

  @pytest.mark.slow
  def test_non_admins_cannot_invite(
    self,
    connection,
    read_connection,
    write_connection,
    config_broker,
    auth_provider,
    inbox,
    api,
  ):
    other_connection = self.make_v1_connection(config_broker, api, auth_provider)
    other_user = other_connection.users(other_connection.user_id).fetch()

    # Non admins can view client pending permissions
    read_connection.clients(read_connection.client_id).pending_permissions().fetch()
    write_connection.clients(write_connection.client_id).pending_permissions().fetch()

    # Non admins can't invite
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.invite(read_connection, other_user.email)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.invite(write_connection, other_user.email)

    # Non admins can't uninvite
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      read_connection.clients(read_connection.client_id).invites().delete(email=other_user.email)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      write_connection.clients(write_connection.client_id).invites().delete(email=other_user.email)

    # Guests can't view, invite, or uninvite
    with connection.create_any_experiment() as e:
      token = connection.experiments(e.id).tokens().create()
      guest = self.make_v1_guest_connection(config_broker, api, token.token)
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        guest.clients(connection.client_id).pending_permissions().fetch()
      guest.client_id = connection.client_id
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        self.invite(guest, other_user.email)
      with RaisesApiException(HTTPStatus.FORBIDDEN):
        guest.clients(connection.client_id).invites().delete(email=other_user.email)

  def test_read_user_cant_see_private_exp(self, connection, read_connection_same_client):
    connection.clients(connection.client_id).update(client_security={"allow_users_to_see_experiments_by_others": False})

    with connection.create_experiment_as(connection.client_id) as e:
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        read_connection_same_client.experiments(e.id).fetch()

  def test_write_user_cant_see_private_exp(self, connection, write_connection_same_client):
    connection.clients(connection.client_id).update(client_security={"allow_users_to_see_experiments_by_others": False})

    with connection.create_experiment_as(connection.client_id) as e:
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        write_connection_same_client.experiments(e.id).fetch()

  def test_admin_user_can_see_private_exp(self, connection, admin_connection_same_client):
    connection.clients(connection.client_id).update(client_security={"allow_users_to_see_experiments_by_others": False})

    with connection.create_experiment_as(connection.client_id) as e:
      admin_connection_same_client.experiments(e.id).fetch()

  def test_read_client_only(self, connection, config_broker, api, auth_provider, api_url):
    other_connection = self.make_v1_connection(config_broker, api, auth_provider)

    client_token = auth_provider.create_client_token(connection.client_id, other_connection.user_id)
    auth_provider.create_membership(other_connection.user_id, connection.organization_id)
    auth_provider.create_permission(other_connection.user_id, connection.client_id, READ)
    client_only_connection = IntegrationTestConnection(api_url, api, client_token=client_token)

    connection.clients(connection.client_id).update(client_security={"allow_users_to_see_experiments_by_others": False})
    with connection.create_any_experiment() as e:
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        client_only_connection.experiments(e.id).fetch()

  def test_write_client_only(self, connection, config_broker, api, auth_provider, api_url):
    other_connection = self.make_v1_connection(config_broker, api, auth_provider)

    client_token = auth_provider.create_client_token(connection.client_id, other_connection.user_id)
    auth_provider.create_membership(other_connection.user_id, connection.organization_id)
    auth_provider.create_permission(other_connection.user_id, connection.client_id, WRITE)
    client_only_connection = IntegrationTestConnection(api_url, api, client_token=client_token)

    connection.clients(connection.client_id).update(client_security={"allow_users_to_see_experiments_by_others": False})
    with connection.create_any_experiment() as e:
      with RaisesApiException(HTTPStatus.NOT_FOUND):
        client_only_connection.experiments(e.id).fetch()

  def test_admin_client_only(self, connection, config_broker, api, auth_provider, api_url):
    other_connection = self.make_v1_connection(config_broker, api, auth_provider)

    client_token = auth_provider.create_client_token(connection.client_id, other_connection.user_id)
    auth_provider.create_membership(other_connection.user_id, connection.organization_id)
    auth_provider.create_permission(other_connection.user_id, connection.client_id, ADMIN)
    client_only_connection = IntegrationTestConnection(api_url, api, client_token=client_token)

    connection.clients(connection.client_id).update(client_security={"allow_users_to_see_experiments_by_others": False})
    with connection.create_any_experiment() as e:
      client_only_connection.experiments(e.id).fetch()

  def test_token_signup_scope(self, owner_connection, config_broker, api, api_url):
    token = owner_connection.clients(owner_connection.client_id).tokens().create()
    connection = IntegrationTestConnection(api_url, api, client_token=token.token)
    assert connection.sessions().fetch().user is None
    assert connection.sessions().fetch().client.id == owner_connection.client_id
    connection.organizations(owner_connection.organization_id).fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.clients(owner_connection.client_id).fetch()
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.clients(owner_connection.client_id).experiments().fetch()
