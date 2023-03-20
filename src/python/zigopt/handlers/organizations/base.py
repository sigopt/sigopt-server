# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.base.handler import Handler
from zigopt.net.errors import NotFoundError


class OrganizationHandler(Handler):
  def __init__(self, services, request, organization_id):
    if organization_id is None:
      raise Exception("Organization id required")

    self.organization_id = organization_id
    self.organization = None
    super().__init__(services, request)

  def find_objects(self):
    return extend_dict(
      super().find_objects(),
      {
        "organization": self._find_organization(self.organization_id),
      },
    )

  def _find_organization(self, organization_id):
    if organization_id:
      organization = self.services.organization_service.find_by_id(
        organization_id,
        include_deleted=False,
      )
      if organization:
        return organization
    raise NotFoundError(f"No organization {organization_id}")

  def can_act_on_objects(self, requested_permission, objects):
    return super().can_act_on_objects(requested_permission, objects) and self.auth.can_act_on_organization(
      self.services, requested_permission, objects["organization"]
    )
