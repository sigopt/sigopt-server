# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime as dt
import time
from http import HTTPStatus

import pytest

from zigopt.common import *
from zigopt.common.sigopt_datetime import current_datetime, get_month_interval
from zigopt.invite.constant import NO_ROLE, USER_ROLE

from integration.base import RaisesApiException
from integration.v1.endpoints.invites.test_base import InviteTestBase
from integration.v1.test_base import V1Base


class TestOrganizations(V1Base):
  @pytest.fixture(params=["prod", "dev"])
  def this_connection(self, request, connection, development_connection):
    if request.param == "dev":
      return development_connection
    return connection

  def test_detail_organization(self, this_connection):
    organization_detail = this_connection.organizations(this_connection.organization_id).fetch()
    assert organization_detail is not None
    assert int(this_connection.organization_id) == int(organization_detail.id)


class TestOrganizationUpdate(V1Base):
  def test_update_name(self, owner_connection):
    organization = owner_connection.organizations(owner_connection.organization_id).fetch()
    updated_organization = owner_connection.organizations(organization.id).update(name="new name")
    assert updated_organization.name == "new name"
    updated_organization = owner_connection.organizations(organization.id).fetch()
    assert updated_organization.name == "new name"

  def test_update_email_domains(self, owner_connection):
    organization = owner_connection.organizations(owner_connection.organization_id).fetch()
    updated_organization = owner_connection.organizations(organization.id).update(email_domains=["fake.com"])
    assert updated_organization.email_domains == ["fake.com"]
    updated_organization = owner_connection.organizations(organization.id).fetch()
    assert updated_organization.email_domains == ["fake.com"]

  def test_update_allow_signup(self, owner_connection):
    organization = owner_connection.organizations(owner_connection.organization_id).fetch()
    updated_organization = owner_connection.organizations(organization.id).update(
      allow_signup_from_email_domains=True,
      email_domains=["fake.com"],
    )
    assert updated_organization.allow_signup_from_email_domains is True
    updated_organization = owner_connection.organizations(organization.id).fetch()
    assert updated_organization.allow_signup_from_email_domains is True
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      owner_connection.organizations(organization.id).update(
        allow_signup_from_email_domains=True,
        email_domains=[],
      )

  def test_update_client_for_email_signup(self, owner_connection):
    organization = owner_connection.organizations(owner_connection.organization_id).fetch()
    updated_organization = owner_connection.organizations(organization.id).update(
      client_for_email_signup=owner_connection.client_id,
    )
    assert updated_organization.client_for_email_signup == owner_connection.client_id
    updated_organization = owner_connection.organizations(organization.id).fetch()
    assert updated_organization.client_for_email_signup == owner_connection.client_id
    with RaisesApiException(HTTPStatus.NOT_FOUND):
      owner_connection.organizations(organization.id).update(
        client_for_email_signup=int(owner_connection.client_id) - 1,
      )

  def test_non_owner_cant_update(self, connection):
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.organizations(connection.organization_id).update(name="new name")
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.organizations(connection.organization_id).update(email_domains=[])
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.organizations(connection.organization_id).update(allow_signup_from_email_domains=True)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.organizations(connection.organization_id).update(client_for_email_signup="1")


class TestOrganizationMemberships(V1Base):
  def test_all_members(self, owner_connection, services):
    memberships = owner_connection.organizations(owner_connection.organization_id).memberships().fetch()
    num_memberships = services.membership_service.count_by_organization_id(owner_connection.organization_id)
    assert len(memberships.data) == num_memberships

  def test_owners_only(self, owner_connection, services):
    owner_memberships = (
      owner_connection.organizations(owner_connection.organization_id).memberships().fetch(membership_type="owner")
    )
    num_owner_memberships = len(
      services.membership_service.find_owners_by_organization_id(owner_connection.organization_id)
    )
    assert len(owner_memberships.data) == num_owner_memberships

  def test_members_only(self, new_organization_owned_by_connection_user, connection, services):
    organization = new_organization_owned_by_connection_user
    member_memberships = connection.organizations(organization.id).memberships().fetch(membership_type="member")
    assert len(member_memberships.data) == 0


class TestOrganizationClients(V1Base):
  def test_retrieve_clients(self, connection, services):
    clients = connection.organizations(connection.organization_id).clients().fetch()
    num_clients = services.client_service.count_by_organization_id(connection.organization_id)
    assert len(clients.data) == num_clients

  def test_add_client_as_owner(self, owner_connection, services):
    client_name = "Test Client"
    owner_connection.organizations(owner_connection.organization_id).clients().create(name=client_name)

    clients = owner_connection.organizations(owner_connection.organization_id).clients().fetch()
    assert len(clients.data) == 2

  def test_add_client_as_member(self, connection, services):
    client_name = "Test Client"
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.organizations(connection.organization_id).clients().create(name=client_name)

    clients = services.client_service.find_by_organization_id(connection.organization_id)

    assert len(clients) == 1


class TestOrganizationExperiments(V1Base):
  def test_list_experiments(self, owner_connection):
    other_client = owner_connection.organizations(owner_connection.organization_id).clients().create(name="Test Client")
    e1 = owner_connection.create_any_experiment(client_id=owner_connection.client_id)
    e2 = owner_connection.create_any_experiment(client_id=other_client.id)

    org_experiments = owner_connection.organizations(owner_connection.organization_id).experiments().fetch(limit=10)
    assert find(org_experiments.data, lambda e: e.id == e1.id)
    assert find(org_experiments.data, lambda e: e.id == e2.id)


class TestOrganizationSuggestions(V1Base):
  @pytest.mark.slow
  def test_count_optimized_runs(self, connection, services):
    # create five suggestions, 1 before the start time, 1 with default rules, 1 as generated suggestion, 1 as queued,
    #    1 after stop time only the default should count as optimized run then expand time boundaries and confirm that
    #    all but generated and queued suggestion are counted
    experiment = connection.create_experiment_as(client_id=connection.client_id)
    connection.experiments(experiment.id).suggestions().create()
    time.sleep(1)
    # often sleeps are a sign of code smells- but I'm not sure how to override the time created on a suggestion, so
    # I'm putting in pauses to make sure that the times are separated out and we get the results we expect
    start_time = current_datetime()
    time.sleep(1)
    connection.experiments(experiment.id).suggestions().create()
    connection.experiments(experiment.id).suggestions().create(
      assignments={
        "a": 1.5,
      }
    )
    connection.experiments(experiment.id).queued_suggestions().create(
      assignments={
        "a": 1.5,
      }
    )
    connection.experiments(experiment.id).suggestions().create()
    time.sleep(1)
    stop_time = current_datetime()
    time.sleep(1)
    connection.experiments(experiment.id).suggestions().create()
    test = services.organization_service.get_optimized_runs_in_billing_cycle(
      connection.organization_id, start_time, stop_time
    )
    assert test == 1
    test = services.organization_service.get_optimized_runs_in_billing_cycle(
      connection.organization_id, start_time - dt.timedelta(seconds=1000), stop_time + dt.timedelta(seconds=1000)
    )
    assert test == 3

  @pytest.mark.slow
  def test_count_all_runs(self, connection, services):
    # create five suggestions, 1 before the start time, 1 with default rules, 1 as generated suggestion, 1 as queued,
    # 1 after stop time only the middle three should count as optimized run then expand time boundaries
    # and confirm that all are counted
    experiment = connection.create_experiment_as(client_id=connection.client_id)
    connection.experiments(experiment.id).suggestions().create()
    time.sleep(1)
    # often sleeps are a sign of code smells- but I'm not sure how to override the time created on a suggestion, so
    # I'm putting in pauses to make sure that the times are separated out and we get the results we expect
    start_time = current_datetime()
    time.sleep(1)
    connection.experiments(experiment.id).suggestions().create()
    connection.experiments(experiment.id).suggestions().create(
      assignments={
        "a": 1.5,
      }
    )
    connection.experiments(experiment.id).queued_suggestions().create(
      assignments={
        "a": 1.5,
      }
    )
    connection.experiments(experiment.id).suggestions().create()
    time.sleep(1)
    stop_time = current_datetime()
    time.sleep(1)
    connection.experiments(experiment.id).suggestions().create()
    test = services.organization_service.get_total_runs_in_billing_cycle(
      connection.organization_id, start_time, stop_time
    )
    assert test == 3
    test = services.organization_service.get_total_runs_in_billing_cycle(
      connection.organization_id, start_time - dt.timedelta(seconds=1000), stop_time + dt.timedelta(seconds=1000)
    )
    assert test == 5

  @pytest.mark.skip(reason="optimized runs by plan bounds no longer relevant")
  def test_create_suggestion_cache(self, connection, services):
    # Set optimized run limit to be high so it won't bother us
    # Create new suggestion, check Redis for existence of cache
    # Compare what's in cache to what's in SQL, ensure they are the same
    # Create two more regular suggestions and a user generated suggestion
    # ensure the SQL and cache values are the same
    # N.B. Because of the way the redis keys work, this has to have correct billing info and
    # use the entire period, not as flexible as the SQL results
    experiment = connection.create_experiment_as(client_id=connection.client_id)
    start_interval, end_interval = get_month_interval()

    connection.experiments(experiment.id).suggestions().create()
    # pylint: disable=protected-access
    test_redis = services.organization_service._get_optimized_runs_in_billing_cycle_cache(
      connection.organization_id,
      start_interval,
      end_interval,
    )
    test_sql = services.organization_service._get_optimized_runs_in_billing_cycle(
      connection.organization_id,
      start_interval,
      end_interval,
    )
    assert int(test_redis) == test_sql
    assert test_sql is not None and test_sql > 0
    connection.experiments(experiment.id).suggestions().create()
    connection.experiments(experiment.id).suggestions().create()
    connection.experiments(experiment.id).suggestions().create(
      assignments={
        "a": 1.5,
      }
    )
    connection.experiments(experiment.id).queued_suggestions().create(
      assignments={
        "a": 1.5,
      }
    )
    connection.experiments(experiment.id).suggestions().create()
    test_redis_2 = services.organization_service._get_optimized_runs_in_billing_cycle_cache(
      connection.organization_id,
      start_interval,
      end_interval,
    )
    test_sql_2 = services.organization_service._get_optimized_runs_in_billing_cycle(
      connection.organization_id,
      start_interval,
      end_interval,
    )
    # pylint: enable=protected-access
    assert int(test_redis_2) == test_sql_2
    assert test_sql_2 is not None and test_sql_2 > 0
    assert test_sql_2 > test_sql


class TestOrganizationPermissions(InviteTestBase):
  def test_list_permissions(self, owner_connection, invitee, invitee_connection, inbox, config_broker):
    permissions = owner_connection.organizations(owner_connection.organization_id).permissions().fetch()
    assert len(permissions.data) == 1
    assert permissions.data[0].is_owner

    other_client = owner_connection.organizations(owner_connection.organization_id).clients().create(name="Test Client")

    owner_connection.clients(other_client.id).invites().create(email=invitee.email, role=USER_ROLE, old_role=NO_ROLE)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)

    permissions = owner_connection.organizations(owner_connection.organization_id).permissions().fetch().data
    assert len(permissions) == 3
    main_client_owner_permission = find(permissions, lambda p: p.client.id == owner_connection.client_id)
    assert main_client_owner_permission
    other_client_owner_permission = find(permissions, lambda p: p.client.id == other_client.id and p.is_owner)
    assert other_client_owner_permission
    other_client_member_permission = find(
      permissions, lambda p: p.client.id == other_client.id and p.user.id == invitee.id
    )
    assert other_client_member_permission
