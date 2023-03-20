# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from integration.service.test_base import ServiceBase


class TagServiceTestBase(ServiceBase):
  @pytest.fixture
  def client(self, services):
    organization = self.make_organization(services, "Tag Test Organization")
    client = self.make_client(services, "Tag Test Client", organization)
    return client

  @pytest.fixture
  def another_client(self, services):
    organization = self.make_organization(services, "Another Tag Test Organization")
    client = self.make_client(services, "Another Tag Test Client", organization)
    return client

  @pytest.fixture
  def tag_service(self, services):
    return services.tag_service

  @classmethod
  def assert_tags_are_equal(cls, tag1, tag2):
    assert tag1.name == tag2.name
    assert tag1.client_id == tag2.client_id
    assert tag1.data == tag2.data
