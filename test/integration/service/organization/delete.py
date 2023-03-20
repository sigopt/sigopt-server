# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.test_base import ServiceBase


class TestOrganizationDelete(ServiceBase):
  def test_delete(self, services):
    organization = self.make_organization(services, "Test Organization")
    assert organization.deleted is False
    services.organization_service.delete(organization)
    assert organization.deleted is True

  def test_delete_persists(self, services):
    organization = self.make_organization(services, "Test Organization")
    services.organization_service.delete(organization)
    services.organization_service.find_by_id(organization.id)
    assert organization.deleted is True

  def test_delete_deleted(self, services):
    organization = self.make_organization(services, "Test Organization")
    services.organization_service.delete(organization)
    services.organization_service.delete(organization)
    assert organization.deleted is True
    services.organization_service.find_by_id(organization.id)
    assert organization.deleted is True

  def test_delete_by_id(self, services):
    organization = self.make_organization(services, "Test Organization")
    with pytest.raises(Exception):
      services.organization_service.delete(organization.id)
