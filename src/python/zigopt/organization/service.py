# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import current_datetime, datetime_to_seconds, get_month_interval, unix_timestamp
from zigopt.experiment.model import Experiment
from zigopt.iam_logging.service import IamEvent, IamResponseStatus
from zigopt.invite.constant import ADMIN_ROLE
from zigopt.invite.model import Invite
from zigopt.json.builder import MembershipJsonBuilder
from zigopt.membership.model import MembershipType
from zigopt.organization.model import Organization
from zigopt.permission.pending.model import PendingPermission
from zigopt.protobuf.gen.client.clientmeta_pb2 import ClientMeta
from zigopt.protobuf.gen.organization.organizationmeta_pb2 import OrganizationMeta
from zigopt.services.base import Service
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class OrganizationService(Service):
  NON_OPTIMIZED_SUGGEESTION_TYPES = (
    UnprocessedSuggestion.Source.USER_CREATED,
    UnprocessedSuggestion.Source.GRID,
    UnprocessedSuggestion.Source.QUEUED_SUGGESTION,
    UnprocessedSuggestion.Source.EXPLICIT_RANDOM,
  )

  def find_by_id(self, organization_id, include_deleted=False):
    return list_get(self.find_by_ids([organization_id], include_deleted=include_deleted), 0)

  def find_by_ids(self, organization_ids, include_deleted=False):
    if organization_ids:
      return self.services.database_service.all(
        self._include_deleted_clause(
          include_deleted,
          self.services.database_service.query(Organization).filter(Organization.id.in_(organization_ids)),
        ),
      )
    else:
      return []

  def _include_deleted_clause(self, include_deleted, q):
    if not include_deleted:
      return q.filter(Organization.date_deleted.is_(None))
    return q

  def _query_all(self, include_deleted=False):
    return self._include_deleted_clause(include_deleted, self.services.database_service.query(Organization))

  def find_all(self, limit=None, before=None, after=None, include_deleted=False):
    q = self._query_all(include_deleted)
    return self.services.query_pager.get_page_results(q, Organization.id, limit=limit, before=before, after=after)

  def count_all(self, limit=None, before=None, after=None, include_deleted=False):
    q = self._query_all(include_deleted)
    return self.services.database_service.count(q)

  def insert(self, organization):
    self.services.database_service.insert(organization)
    return organization

  def delete(self, organization):
    date_deleted = current_datetime()
    did_update = self.delete_by_id(organization.id, date_deleted=date_deleted)
    if did_update:
      organization.date_deleted = date_deleted
    return did_update

  def delete_by_id(self, organization_id, date_deleted=None):
    date_deleted = date_deleted or current_datetime()
    self.services.invite_service.delete_by_organization_id(organization_id)
    self.services.membership_service.delete_by_organization_id(organization_id)
    return bool(
      self.services.database_service.update_one_or_none(
        self.services.database_service.query(Organization).filter(Organization.id == organization_id),
        {Organization.date_deleted: date_deleted},
      )
    )

  def set_up_new_organization(
    self,
    organization_name,
    client_name,
    user,
    allow_users_to_see_experiments_by_others,
    requestor,
    academic=None,
    user_is_owner=False,
  ):
    organization_meta = OrganizationMeta(academic=academic)
    organization = Organization(name=organization_name, organization_meta=organization_meta)

    self.services.organization_service.insert(organization)

    meta = ClientMeta()
    meta.date_created = unix_timestamp()

    meta.client_security.SetFieldIfNotNone(
      "allow_users_to_see_experiments_by_others", allow_users_to_see_experiments_by_others
    )

    client = Client(
      organization_id=organization.id,
      name=client_name,
      client_meta=meta,
    )
    self.services.client_service.insert(client)
    self.services.project_service.create_example_for_client(client_id=client.id)

    if user_is_owner:
      assert user is not None
      membership = self.services.membership_service.insert(
        user_id=user.id,
        organization_id=client.organization_id,
        membership_type=MembershipType.owner,
      )
      self.services.iam_logging_service.log_iam(
        requestor=requestor,
        event_name=IamEvent.MEMBERSHIP_CREATE,
        request_parameters={
          "user_id": user.id,
          "membership_type": MembershipType.owner.value,
          "organization_id": organization.id,
        },
        response_element=MembershipJsonBuilder.json(membership, organization, user),
        response_status=IamResponseStatus.SUCCESS,
      )

    return (organization, client)

  def merge_organizations_into_destination(self, dest_organization_id, organization_ids, requestor):
    dest_organization = self.find_by_id(dest_organization_id)

    for organization_id in organization_ids:
      clients = self.services.client_service.find_by_organization_id(organization_id)

      memberships = self.services.membership_service.find_by_organization_id(organization_id)
      for m in memberships:
        self.services.membership_service.create_if_not_exists(
          user_id=m.user_id, organization_id=dest_organization.id, membership_type=MembershipType.member
        )

        # Create permission for each client if it is an owner membership in the source org
        # and the user is not an owner in the destination org
        destination_membership = self.services.membership_service.find_by_user_and_organization(
          m.user_id, dest_organization.id
        )
        if m.is_owner and not destination_membership.is_owner:
          user = self.services.user_service.find_by_id(m.user_id)
          for c in clients:
            self.services.permission_service.upsert_from_role(ADMIN_ROLE, c, user, requestor=requestor)

        # Delete their permissions in the source organization so they aren't copied over in the cascade
        if not m.is_owner and destination_membership.is_owner:
          self.services.permission_service.delete_by_organization_and_user(m.organization_id, m.user_id)

      invites_to_organization = self.services.invite_service.find_by_organization_id(organization_id)
      for i in invites_to_organization:
        # Cascades organization_id to pending_permissions.organization_id
        self.services.database_service.update(
          self.services.database_service.query(Invite).filter(Invite.id == i.id), {Invite.organization_id: None}
        )

      for c in clients:
        # Cascades to roles.organization_id
        self.services.database_service.update(
          self.services.database_service.query(Client).filter(Client.id == c.id),
          {Client.organization_id: dest_organization.id},
        )

      for i in invites_to_organization:
        existing_invite = self.services.invite_service.find_by_email_and_organization(i.email, dest_organization.id)
        if existing_invite:
          self.services.invite_service.delete_by_id(i.id)
        else:
          self.services.database_service.update(
            self.services.database_service.query(Invite).filter(Invite.id == i.id),
            {Invite.organization_id: dest_organization.id},
          )

        pending_permissions = self.services.pending_permission_service.find_by_invite_id(i.id)
        for p in pending_permissions:
          self.services.database_service.update(
            self.services.database_service.query(PendingPermission).filter(PendingPermission.id == p.id),
            {PendingPermission.organization_id: dest_organization.id},
          )

      self.services.membership_service.delete_by_organization_id(organization_id)
      self.delete_by_id(organization_id)

  def get_optimized_runs_in_billing_cycle(self, organization_id, start_date, end_date, look_in_cache=True):
    if look_in_cache:
      count = self._get_optimized_runs_in_billing_cycle_cache(organization_id, start_date, end_date)
      if count is not None:
        return count
    count = self._get_optimized_runs_in_billing_cycle(organization_id, start_date, end_date)
    self._write_optimized_runs_in_billing_cycle_cache(organization_id, start_date, end_date, count)
    return count

  def _get_optimized_runs_in_billing_cycle_cache(self, organization_id, start_date, end_date):
    optimized_runs_key = self.services.redis_key_service.create_optimized_run_by_org_billing_key(
      organization_id, start_date
    )
    count = None
    with self.services.exception_logger.tolerate_exceptions(Exception):
      count = self.services.redis_service.get(optimized_runs_key)
    return napply(count, int)

  def _get_optimized_runs_in_billing_cycle(self, organization_id, start_date, end_date):
    q = (
      self.services.database_service.query(Client)
      .join(Experiment, Client.id == Experiment.client_id)
      .join(UnprocessedSuggestion, UnprocessedSuggestion.experiment_id == Experiment.id)
      .filter(Client.organization_id == organization_id)
      .filter(UnprocessedSuggestion.source.notin_(self.NON_OPTIMIZED_SUGGEESTION_TYPES))
    )
    if start_date is not None:
      q = q.filter(UnprocessedSuggestion.generated_time >= datetime_to_seconds(start_date))
    if end_date is not None:
      q = q.filter(UnprocessedSuggestion.generated_time < datetime_to_seconds(end_date))
    count = self.services.database_service.count(q)
    return count

  def _write_optimized_runs_in_billing_cycle_cache(self, organization_id, start_date, end_date, count):
    optimized_runs_key = self.services.redis_key_service.create_optimized_run_by_org_billing_key(
      organization_id, start_date
    )
    expire_at = None
    if end_date is not None:
      # add buffer to allow for clock drift. Since we use start_date for the key, we don't risk
      # miscounting the optimized runs after end_date - once they have a new window, they'll use a new key
      end_buffer = datetime.timedelta(days=1)
      expire_at = end_date + end_buffer
    with self.services.exception_logger.tolerate_exceptions(Exception):
      self.services.redis_service.set(optimized_runs_key, count)
      if expire_at is not None:
        self.services.redis_service.set_expire_at(optimized_runs_key, expire_at)

  def get_optimized_runs_from_organization_id(self, organization_id):
    start_interval, end_interval = get_month_interval()
    return self.get_optimized_runs_in_billing_cycle(organization_id, start_interval, end_interval)

  def get_total_runs_from_organization_id(self, organization_id):
    start_interval, end_interval = get_month_interval()
    return self.get_total_runs_in_billing_cycle(organization_id, start_interval, end_interval)

  def get_total_runs_in_billing_cycle(self, organization_id, start_date, end_date):
    q = (
      self.services.database_service.query(Client)
      .join(Experiment, Client.id == Experiment.client_id)
      .join(UnprocessedSuggestion, UnprocessedSuggestion.experiment_id == Experiment.id)
      .filter(Client.organization_id == organization_id)
    )
    if start_date is not None:
      q = q.filter(UnprocessedSuggestion.generated_time >= datetime_to_seconds(start_date))
    if end_date is not None:
      q = q.filter(UnprocessedSuggestion.generated_time < datetime_to_seconds(end_date))
    count = self.services.database_service.count(q)
    return count
