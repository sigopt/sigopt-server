# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.service.test_base import ServiceBase


class TestOrganizationServiceMethods(ServiceBase):
  def test_find_by_id(self, services):
    organization = self.make_organization(services, "Test Organization")
    o = services.organization_service.find_by_id(organization.id)
    assert o.id == organization.id
    assert o.name == organization.name

  def test_find_by_ids(self, services):
    org1 = self.make_organization(services, "Test Organization 1")
    org2 = self.make_organization(services, "Test Organization 2")
    found_orgs = services.organization_service.find_by_ids([org1.id, org2.id])
    assert found_orgs[0].id == org1.id
    assert found_orgs[0].name == org1.name
    assert found_orgs[1].id == org2.id
    assert found_orgs[1].name == org2.name

  def test_find_all(self, services):
    org1 = self.make_organization(services, "Test Organization 1")
    org2 = self.make_organization(services, "Test Organization 2")
    found_orgs = services.organization_service.find_all()
    sorted_found_orgs = sorted(found_orgs, key=lambda x: x.id, reverse=True)
    assert org1.id == sorted_found_orgs[1].id
    assert org1.name == sorted_found_orgs[1].name
    assert org2.id == sorted_found_orgs[0].id
    assert org2.name == sorted_found_orgs[0].name

    services.organization_service.delete(org2)
    all_orgs_after_deleted = services.organization_service.find_all()
    assert len(all_orgs_after_deleted) == len(sorted_found_orgs) - 1

  def test_count_all(self, services):
    num_orgs_before = services.organization_service.count_all()
    self.make_organization(services, "Test Organization 1")
    self.make_organization(services, "Test Organization 2")
    num_orgs_after = services.organization_service.count_all()
    assert num_orgs_after - num_orgs_before == 2
