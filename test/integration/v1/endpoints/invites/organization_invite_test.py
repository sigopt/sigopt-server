# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# Black and isort are engaged in a war over the imports
"""
isort:skip_file
"""

from http import HTTPStatus

import pytest
from integration.auth import AuthProvider
from integration.base import RaisesApiException
from integration.v1.endpoints.invites.test_base import InviteTestBase
from zigopt.common import *
from zigopt.invite.constant import ADMIN_ROLE, NO_ROLE, READ_ONLY_ROLE, USER_ROLE
from zigopt.membership.model import Membership, MembershipType
from zigopt.user.model import User, normalize_email

MEMBER = MembershipType.member.value
OWNER = MembershipType.owner.value


class OrganizationInviteTestBase(InviteTestBase):
  @pytest.fixture(autouse=True)
  def check_invites(self, config_broker):
    if not config_broker.get("email.verify", True):
      pytest.skip("Since all users have verified emails, no invite object is created")

  def invite(self, connection, organization_id, membership_type, client_invites, invitee):
    return self.invite_email(connection, organization_id, membership_type, client_invites, invitee.email)

  def invite_email(self, connection, organization_id, membership_type, client_invites, email):
    return (
      connection.organizations(organization_id)
      .invites()
      .create(
        email=email,
        client_invites=client_invites,
        membership_type=membership_type,
      )
    )

  def uninvite(self, connection, organization_id, invitee):
    self.uninvite_email(connection, organization_id, invitee.email)

  def uninvite_email(self, connection, organization_id, email):
    connection.organizations(organization_id).invites().delete(email=email)

  @pytest.fixture
  def owner_organization_id(self, owner_connection):
    return owner_connection.organization_id

  @pytest.fixture
  def owner_client_id(self, owner_connection):
    return owner_connection.client_id


class TestInvite(OrganizationInviteTestBase):
  def test_invite_params(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
  ):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      owner_connection.organizations(owner_organization_id).invites().create(
        email=AuthProvider.randomly_generated_email(),
      )

    owner_connection.organizations(owner_organization_id).invites().create(
      email=AuthProvider.randomly_generated_email(),
      membership_type=OWNER,
    )
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      owner_connection.organizations(owner_organization_id).invites().create(
        email=AuthProvider.randomly_generated_email(), membership_type=MEMBER
      )

    owner_connection.organizations(owner_organization_id).invites().create(
      email=AuthProvider.randomly_generated_email(),
      membership_type=MEMBER,
      client_invites=[dict(id=owner_client_id, role=USER_ROLE)],
    )

  def test_invite_create(
    self,
    owner_connection,
    owner_organization_id,
    owner_client_id,
    invitee_connection,
    invitee,
    config_broker,
  ):
    invite = self.invite(
      owner_connection,
      owner_organization_id,
      MEMBER,
      client_invites=[dict(id=owner_client_id, role=USER_ROLE)],
      invitee=invitee,
    )

    assert invite.email == normalize_email(invitee.email)
    assert invite.membership_type == MEMBER
    assert invite.organization == str(owner_organization_id)
    assert not invite.invite_code

  def test_invite_no_verify(
    self, owner_connection, owner_client_id, owner_organization_id, invitee_connection, invitee, config_broker
  ):
    if not self.email_needs_verify(config_broker):
      pytest.skip()

    client_invites = [dict(id=owner_client_id, role=USER_ROLE)]
    self.invite(owner_connection, owner_organization_id, MEMBER, client_invites, invitee)

    with RaisesApiException(HTTPStatus.NOT_FOUND):
      invitee_connection.clients(owner_client_id).permissions().fetch()

  def test_cant_invite_invalid_email_domain(
    self,
    owner_connection,
    owner_organization_id,
    config_broker,
    inbox,
  ):
    domain = "mydomain.com"
    owner_connection.organizations(owner_organization_id).update(email_domains=[domain])
    valid_email = f"someonee@{domain}"
    invalid_email = "someone@anotherdomain.com"
    subdomain_email = f"someone@fake.{domain}"
    substring_email = f"someone@fake{domain}"

    invite = self.invite_email(
      owner_connection,
      owner_organization_id,
      OWNER,
      client_invites=[],
      email=valid_email,
    )
    inbox.wait_for_email(valid_email, search_term=invite.invite_code)

    for email in (invalid_email, subdomain_email, substring_email):
      with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
        self.invite_email(
          owner_connection,
          owner_organization_id,
          OWNER,
          client_invites=[],
          email=email,
        )
      assert f"from the following domains: {domain}" in str(e)

  @pytest.mark.skip(reason="plans dont support this, convert to configuration setting")
  def test_invite_arbitrary_email_domains(
    self,
    owner_connection,
    owner_organization_id,
    config_broker,
    inbox,
  ):
    email = "someone-else@notnotsigopt.ninja"
    invite = self.invite_email(
      owner_connection,
      owner_organization_id,
      OWNER,
      client_invites=[],
      email=email,
    )
    inbox.wait_for_email(email, search_term=invite.invite_code)

  def test_invite_member_to_single_client(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee_connection,
    invitee,
    inbox,
    config_broker,
  ):
    client_invites = [dict(id=owner_client_id, role=USER_ROLE)]
    self.invite(owner_connection, owner_organization_id, MEMBER, client_invites, invitee)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 1
    assert invites[0].email == invitee.email
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    all_permissions = invitee_connection.clients(owner_client_id).permissions().fetch().data
    per = find(all_permissions, lambda p: p.user.id == invitee.id)
    assert per

  def test_invite_member_to_multiple_clients(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee_connection,
    invitee,
    inbox,
    config_broker,
  ):
    another_client = owner_connection.organizations(owner_organization_id).clients().create(name="Test Client")
    client_invites = [dict(id=owner_client_id, role=USER_ROLE), dict(id=another_client.id, role=USER_ROLE)]
    self.invite(owner_connection, owner_organization_id, MEMBER, client_invites, invitee)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    first_client_permissions = invitee_connection.clients(owner_client_id).permissions().fetch().data
    second_client_permissions = invitee_connection.clients(owner_client_id).permissions().fetch().data
    first_per = find(first_client_permissions, lambda p: p.user.id == invitee.id)
    assert first_per
    second_per = find(second_client_permissions, lambda p: p.user.id == invitee.id)
    assert second_per

  def test_invite_user_as_member(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee_connection,
    invitee,
    inbox,
    config_broker,
  ):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    client_invites = [dict(id=owner_client_id, role=USER_ROLE)]
    self.invite(owner_connection, owner_organization_id, MEMBER, client_invites, invitee)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 0
    all_permissions = invitee_connection.clients(owner_client_id).permissions().fetch().data
    per = find(all_permissions, lambda p: p.user.id == invitee.id)
    assert per

  def test_invite_email_as_owner(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee_connection,
    invitee,
    inbox,
    config_broker,
  ):
    self.invite(owner_connection, owner_organization_id, OWNER, [], invitee)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 1
    assert invites[0].email == invitee.email
    assert invites[0].membership_type == "owner"
    self.verify_email(invitee, invitee_connection, inbox, config_broker)

  def test_invite_user_as_owner(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee_connection,
    invitee,
    inbox,
    config_broker,
  ):
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    self.invite(owner_connection, owner_organization_id, OWNER, [], invitee)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 0
    memberships = owner_connection.organizations(owner_organization_id).memberships().fetch().data
    invited_membership = find(memberships, lambda m: m.user.email == invitee.email)
    assert invited_membership is not None
    assert invited_membership.type == MembershipType.owner.value

  def test_cant_create_user_if_inviter_no_longer_member(
    self,
    owner_connection,
    owner_client_id,
    connection,
    owner_organization_id,
    invitee_connection,
    invitee,
    inbox,
    config_broker,
    services,
  ):
    self.invite(owner_connection, owner_organization_id, OWNER, [], invitee)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 1
    services.membership_service.delete_by_organization_id(owner_organization_id)
    # At this point the owner just got deleted out of the organization, so all the confirmations
    # need to be done through service queries, not through the REST API calls
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    invites = services.invite_service.find_by_organization_id(owner_organization_id)
    assert len(invites) == 0
    invited_membership = (
      services.database_service.query(Membership)
      .join(User, User.id == Membership.user_id)
      .filter(Membership.organization_id == owner_organization_id)
      .filter(User.email == invitee.email)
    )
    assert invited_membership.count() == 0

  def test_normal_invite_must_contain_clients(
    self,
    owner_connection,
    owner_organization_id,
    invitee,
  ):
    client_invites = []
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.invite(owner_connection, owner_organization_id, MEMBER, client_invites, invitee)

  def test_invite_must_be_new_email(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee,
  ):
    client_invites = [dict(id=owner_client_id, role=USER_ROLE)]
    self.invite(owner_connection, owner_organization_id, MEMBER, client_invites, invitee)
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.invite(owner_connection, owner_organization_id, OWNER, client_invites, invitee)

  def test_user_cannot_modify_own_role(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
  ):
    client_invites = [dict(id=owner_client_id, role=USER_ROLE)]
    current_user = owner_connection.users(owner_connection.user_id).fetch()
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.invite_email(owner_connection, owner_organization_id, MEMBER, client_invites, current_user.email)

  def test_write_user_cant_invite(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee_connection,
    invitee,
    second_invitee,
    inbox,
    config_broker,
  ):
    self.invite(owner_connection, owner_organization_id, MEMBER, [dict(id=owner_client_id, role=USER_ROLE)], invitee)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.invite(
        invitee_connection, owner_organization_id, MEMBER, [dict(id=owner_client_id, role=USER_ROLE)], second_invitee
      )

  def test_admin_user_cant_invite(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee_connection,
    invitee,
    second_invitee,
    second_invitee_connection,
    inbox,
    config_broker,
  ):
    self.invite(owner_connection, owner_organization_id, MEMBER, [dict(id=owner_client_id, role=ADMIN_ROLE)], invitee)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      self.invite(
        invitee_connection, owner_organization_id, MEMBER, [dict(id=owner_client_id, role=USER_ROLE)], second_invitee
      )


class TestUpdate(OrganizationInviteTestBase):
  @pytest.fixture
  def member_invite(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee,
  ):
    client_invites = [dict(id=owner_client_id, role=USER_ROLE)]
    return self.invite(owner_connection, owner_organization_id, MEMBER, client_invites, invitee)

  @pytest.fixture
  def owner_invite(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee,
    config_broker,
  ):
    return self.invite(owner_connection, owner_organization_id, OWNER, [], invitee)

  @pytest.fixture
  def another_client(
    self,
    owner_connection,
    owner_organization_id,
  ):
    return owner_connection.organizations(owner_organization_id).clients().create(name="Another Test Client")

  @pytest.fixture
  def member_all_invite(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee,
    another_client,
  ):
    client_invites = [dict(id=owner_client_id, role=USER_ROLE), dict(id=another_client.id, role=USER_ROLE)]
    return self.invite(owner_connection, owner_organization_id, MEMBER, client_invites, invitee)

  @pytest.fixture
  def invite_route(
    self,
    owner_connection,
    owner_organization_id,
  ):
    return owner_connection.organizations(owner_organization_id).invites

  def check_invites_match(self, updated_invite, fetched_invites):
    assert len(fetched_invites) == 1
    (invite,) = fetched_invites
    assert invite.id == updated_invite.id
    assert invite.email == updated_invite.email
    assert invite.membership_type == updated_invite.membership_type
    pp_set = lambda pps: frozenset(pp.client for pp in pps)
    assert pp_set(invite.pending_permissions) == pp_set(updated_invite.pending_permissions)

  def test_add_client_to_invite(
    self,
    invite_route,
    member_invite,
    another_client,
  ):
    for role, old_role in [
      (READ_ONLY_ROLE, NO_ROLE),
      (USER_ROLE, READ_ONLY_ROLE),
      (ADMIN_ROLE, USER_ROLE),
    ]:
      updated_invite = invite_route(member_invite.id).update(
        client_invites=[
          dict(
            id=another_client.id,
            role=role,
            old_role=old_role,
          )
        ]
      )
      fetched_invites = invite_route().fetch().data
      self.check_invites_match(updated_invite, fetched_invites)
      assert updated_invite.id == member_invite.id
      assert updated_invite.email == member_invite.email
      assert updated_invite.membership_type == MEMBER
      assert len(updated_invite.pending_permissions) == 2
      new_pending_permission = find(updated_invite.pending_permissions, lambda pp: pp.client == another_client.id)
      assert new_pending_permission is not None
      assert new_pending_permission.role == role

  def test_update_invite(
    self,
    invite_route,
    owner_client_id,
    member_all_invite,
    another_client,
  ):
    updated_invite = invite_route(member_all_invite.id).update(
      client_invites=[
        dict(
          id=another_client.id,
          role=NO_ROLE,
          old_role=USER_ROLE,
        )
      ]
    )
    fetched_invites = invite_route().fetch().data
    self.check_invites_match(updated_invite, fetched_invites)
    assert updated_invite.id == member_all_invite.id
    assert updated_invite.email == member_all_invite.email
    assert updated_invite.membership_type == MEMBER
    assert len(updated_invite.pending_permissions) == 1
    (old_pending_permission,) = updated_invite.pending_permissions
    assert old_pending_permission.client == owner_client_id

  def test_remove_client_from_invite(
    self,
    invite_route,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    member_all_invite,
    invitee,
  ):
    assert len(member_all_invite.pending_permissions) == 2
    owner_connection.clients(owner_client_id).invites().delete(email=invitee.email)
    updated_invites = invite_route().fetch().data
    updated_invite = find(updated_invites, lambda i: i.id == member_all_invite.id)
    assert len(updated_invite.pending_permissions) == 1

  def test_remove_lonely_client_fails(
    self,
    invite_route,
    owner_client_id,
    member_invite,
  ):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      invite_route(member_invite.id).update(client_invites=[dict(id=owner_client_id, role=NO_ROLE, old_role=USER_ROLE)])
    self.check_invites_match(member_invite, invite_route().fetch().data)

  def test_promote_invite(
    self,
    invite_route,
    member_invite,
  ):
    for _ in range(2):
      updated_invite = invite_route(member_invite.id).update(membership_type=OWNER)
      fetched_invites = invite_route().fetch().data
      self.check_invites_match(updated_invite, fetched_invites)
      assert updated_invite.id == member_invite.id
      assert updated_invite.email == member_invite.email
      assert updated_invite.membership_type == OWNER
      assert not updated_invite.pending_permissions

  def test_promote_fails_with_clients(
    self,
    invite_route,
    owner_client_id,
    member_invite,
  ):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      invite_route(member_invite.id).update(
        membership_type=OWNER, client_invites=[dict(id=owner_client_id, role=USER_ROLE)]
      )
    self.check_invites_match(member_invite, invite_route().fetch().data)

  def test_demote_invite(
    self,
    invite_route,
    owner_client_id,
    owner_invite,
  ):
    updated_invite = invite_route(owner_invite.id).update(
      membership_type=MEMBER, client_invites=[dict(id=owner_client_id, role=USER_ROLE)]
    )
    fetched_invites = invite_route().fetch().data
    self.check_invites_match(updated_invite, fetched_invites)
    assert updated_invite.membership_type == MEMBER
    assert len(updated_invite.pending_permissions) == 1
    (pending_permission,) = updated_invite.pending_permissions
    assert pending_permission.client == owner_client_id
    assert pending_permission.role == USER_ROLE

  def test_demote_fails_without_clients(
    self,
    invite_route,
    owner_invite,
  ):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      invite_route(owner_invite.id).update(membership_type=MEMBER, client_invites=[])
    self.check_invites_match(owner_invite, invite_route().fetch().data)


class TestUninvite(OrganizationInviteTestBase):
  def test_uninvite_accepted_normal_user(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee,
  ):
    client_invites = [dict(id=owner_client_id, role=USER_ROLE)]
    self.invite(owner_connection, owner_organization_id, MEMBER, client_invites, invitee)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 1
    assert invites[0].email == invitee.email
    owner_connection.organizations(owner_organization_id).invites().delete(email=invitee.email)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 0

  def test_uninvite_pending_normal_user(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
  ):
    client_invites = [dict(id=owner_client_id, role=USER_ROLE)]
    email = "testuser@notsigopt.ninja"
    self.invite_email(owner_connection, owner_organization_id, MEMBER, client_invites, email)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 1
    assert invites[0].email == email
    owner_connection.organizations(owner_organization_id).invites().delete(email=email)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 0

  def test_uninvite_pending_owner(
    self,
    owner_connection,
    owner_organization_id,
  ):
    email = "testuser@notsigopt.ninja"
    self.invite_email(owner_connection, owner_organization_id, OWNER, [], email)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 1
    assert invites[0].email == email
    owner_connection.organizations(owner_organization_id).invites().delete(email=email)
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 0

  def test_uninvitee_must_exist(
    self,
    owner_connection,
    owner_organization_id,
  ):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.uninvite_email(owner_connection, owner_organization_id, "nonexistentemail@notsigopt.ninja")

  def test_cannot_uninvite_invited_owner(
    self,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    invitee_connection,
    invitee,
    inbox,
    config_broker,
  ):
    self.invite(owner_connection, owner_organization_id, OWNER, [], invitee)
    self.verify_email(invitee, invitee_connection, inbox, config_broker)
    all_permissions = invitee_connection.clients(owner_client_id).permissions().fetch().data
    per = find(all_permissions, lambda p: p.user.id == invitee.id)
    assert per
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      self.uninvite(owner_connection, owner_organization_id, invitee)


class TestInvitesList(OrganizationInviteTestBase):
  def test_can_filter_by_membership_type(
    self,
    services,
    owner_connection,
    owner_client_id,
    owner_organization_id,
    config_broker,
  ):
    client_invites = [dict(id=owner_client_id, role=USER_ROLE)]
    self.invite_email(owner_connection, owner_organization_id, OWNER, [], "1@notsigopt.ninja")
    self.invite_email(owner_connection, owner_organization_id, MEMBER, client_invites, "2@notsigopt.ninja")
    self.invite_email(owner_connection, owner_organization_id, MEMBER, client_invites, "3@notsigopt.ninja")
    invites = owner_connection.organizations(owner_organization_id).invites().fetch().data
    assert len(invites) == 3
    invites = owner_connection.organizations(owner_organization_id).invites().fetch(membership_type=MEMBER).data

    assert len(invites) == 2
    invites = owner_connection.organizations(owner_organization_id).invites().fetch(membership_type=OWNER).data
    assert len(invites) == 1


class TestMembershipChange(OrganizationInviteTestBase):
  def test_elevate_membership_to_owner(
    self,
    services,
    owner_connection_same_organization,
    connection,
    inbox,
    config_broker,
  ):
    memberships = connection.users(connection.user_id).memberships().fetch()
    membership = find(memberships.data, lambda m: m.organization.id == connection.organization_id)
    assert membership.type == MEMBER

    owner_connection_same_organization.organizations(connection.organization_id).invites().create(
      email=connection.email,
      membership_type=OWNER,
    )

    memberships = connection.users(connection.user_id).memberships().fetch()
    membership = find(memberships.data, lambda m: m.organization.id == connection.organization_id)
    assert membership.type == OWNER

  def test_error_membership_update(
    self,
    services,
    owner_connection_same_organization,
    connection,
    inbox,
    config_broker,
  ):
    owner_connection_same_organization.organizations(connection.organization_id).invites().create(
      email=connection.email,
      membership_type=OWNER,
    )

    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      owner_connection_same_organization.organizations(connection.organization_id).invites().create(
        email=connection.email,
        membership_type=OWNER,
      )
