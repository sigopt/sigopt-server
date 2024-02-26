# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections.abc import Sequence

from sqlalchemy.orm import Query
from sqlalchemy.sql.expression import or_, tuple_

from zigopt.common import *
from zigopt.membership.model import Membership, MembershipType
from zigopt.permission.model import Permission
from zigopt.services.base import Service


class MembershipService(Service):
  def _owners_only_clause(self, query: Query) -> Query:
    return query.filter(Membership.membership_type == MembershipType.owner)

  def find_by_organization_id(self, organization_id: int) -> Sequence[Membership]:
    return self.services.database_service.all(
      self.services.database_service.query(Membership).filter_by(organization_id=organization_id),
    )

  def find_by_user_id(self, user_id: int) -> Sequence[Membership]:
    return self.services.database_service.all(
      self.services.database_service.query(Membership).filter_by(user_id=user_id),
    )

  def find_by_user_and_organization(self, user_id: int, organization_id: int) -> Membership | None:
    return self.services.database_service.one_or_none(
      self.services.database_service.query(Membership)
      .filter_by(user_id=user_id)
      .filter_by(organization_id=organization_id),
    )

  def find_by_users_and_organizations(
    self, user_ids: Sequence[int], organization_ids: Sequence[int]
  ) -> Sequence[Membership]:
    if not user_ids or not organization_ids:
      return []
    return self.services.database_service.all(
      self.services.database_service.query(Membership)
      .filter(Membership.user_id.in_(distinct(user_ids)))
      .filter(Membership.organization_id.in_(distinct(organization_ids))),
    )

  def find_owners_by_user_id(self, user_id: int) -> Sequence[Membership]:
    return self.services.database_service.all(
      self._owners_only_clause(self.services.database_service.query(Membership).filter_by(user_id=user_id))
    )

  def find_owners_by_organization_id(self, organization_id: int) -> Sequence[Membership]:
    return self.services.database_service.all(
      self._owners_only_clause(
        self.services.database_service.query(Membership).filter_by(organization_id=organization_id)
      )
    )

  def organizations_with_other_owners(self, organization_ids: Sequence[int], user_id: int) -> Sequence[Membership]:
    return self.services.database_service.all(
      self._owners_only_clause(
        self.services.database_service.query(Membership)
        .filter(Membership.organization_id.in_(organization_ids))
        .filter(Membership.user_id != user_id)
      )
    )

  def organizations_with_other_non_owners(self, organization_ids: Sequence[int], user_id: int) -> Sequence[Membership]:
    return self.services.database_service.all(
      self.services.database_service.query(Membership)
      .filter(Membership.organization_id.in_(organization_ids))
      .filter(Membership.user_id != user_id)
      .filter(Membership.membership_type != MembershipType.owner)
    )

  def count_by_organization_id(self, organization_id: int) -> int:
    return self.services.database_service.count(
      self.services.database_service.query(Membership).filter_by(organization_id=organization_id),
    )

  # NOTE: This function determines if user1 is visible to user2 based on their memberships.
  # Users are mutually visible if they are members of the same organization
  # and at least one of them is an owner of that organization.
  def users_are_mutually_visible(self, user1_id: int, user2_id: int) -> bool:
    def membership_subquery(user_id):
      return (self.services.database_service.query(Membership).filter_by(user_id=user_id)).subquery()

    user1_membership_query = membership_subquery(user1_id)
    user2_membership_query = membership_subquery(user2_id)
    return self.services.database_service.exists(
      self.services.database_service.query(user1_membership_query)
      .join(
        user2_membership_query, (user1_membership_query.c.organization_id == user2_membership_query.c.organization_id)
      )
      .filter(
        or_(
          user1_membership_query.c.membership_type == MembershipType.owner,
          user2_membership_query.c.membership_type == MembershipType.owner,
        )
      )
    )

  def user_is_owner_for_organization(self, user_id: int, organization_id: int) -> bool:
    return self.services.database_service.exists(
      self._owners_only_clause(
        self.services.database_service.query(Membership)
        .filter_by(user_id=user_id)
        .filter_by(organization_id=organization_id)
      )
    )

  def delete(self, membership: Membership) -> int:
    return self.delete_by_organization_and_user(
      organization_id=membership.organization_id,
      user_id=membership.user_id,
    )

  def delete_by_organization_id(self, organization_id: int) -> int:
    if not organization_id:
      raise ValueError(f"Cannot delete a membership with organization_id: `{organization_id}`!")
    return self.services.database_service.delete(
      self.services.database_service.query(Membership).filter_by(organization_id=organization_id)
    )

  # We define a stray membership as one that is not an owner membership, and has no permissions
  def delete_stray_memberships_by_organization(self, organization_id: int) -> int:
    stray_memberships = (
      self.services.database_service.query(Membership.user_id, Membership.organization_id)
      .filter(Membership.organization_id == organization_id)
      .filter(Membership.membership_type != MembershipType.owner)
      .outerjoin(Permission)
      .filter(Permission.id.is_(None))
    )
    return self.services.database_service.delete(
      self.services.database_service.query(Membership).filter(
        tuple_(Membership.user_id, Membership.organization_id).in_(stray_memberships.subquery())
      ),
    )

  def delete_by_organization_and_user(self, organization_id: int, user_id: int) -> int:
    if not (user_id and organization_id):
      raise ValueError(
        "Cannot delete a membership without both a user_id and an organization_id. "
        f"User: {user_id}, organization: {organization_id}"
      )
    result = self.services.database_service.delete(
      self.services.database_service.query(Membership)
      .filter_by(user_id=user_id)
      .filter_by(organization_id=organization_id)
    )
    return result

  def delete_by_user_id(self, user_id: int) -> int:
    if not user_id:
      raise ValueError(f"Cannot delete a membership with user_id: `{user_id}`!")
    result = self.services.database_service.delete(
      self.services.database_service.query(Membership).filter_by(user_id=user_id)
    )
    return result

  def insert(self, user_id: int, organization_id: int, **kwargs) -> Membership:
    if not (user_id and organization_id):
      raise ValueError(
        "Cannot create a membership without both a user_id and an organization_id. "
        f"User: {user_id}, organization: {organization_id}"
      )
    membership = Membership(user_id=user_id, organization_id=organization_id, **kwargs)
    self.services.database_service.insert(membership)
    return membership

  def create_if_not_exists(
    self, user_id: int, organization_id: int, membership_type: MembershipType | None = None, **kwargs
  ) -> Membership:
    if existing := self.find_by_user_and_organization(user_id, organization_id):
      return existing
    return self.insert(user_id=user_id, organization_id=organization_id, membership_type=membership_type, **kwargs)

  def elevate_to_owner(self, membership: Membership) -> int:
    membership.membership_type = MembershipType.owner
    return self.services.database_service.update_one(
      self.services.database_service.query(Membership)
      .filter(Membership.user_id == membership.user_id)
      .filter(Membership.organization_id == membership.organization_id),
      {Membership.membership_type: MembershipType.owner},
    )
