# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.json.builder import OrganizationJsonBuilder
from zigopt.organization.model import Organization
from zigopt.protobuf.gen.organization.organizationmeta_pb2 import OrganizationMeta

from sigopttest.json.builder.test_base import ORGANIZATION_FIELDS, BuilderTestBase


class TestOrganizationJsonBuilder(BuilderTestBase):
  @pytest.mark.parametrize("academic", [True, False])
  def test_fields(self, academic):
    organization = Organization(
      id=self.organization_id,
      name="an organization",
      organization_meta=OrganizationMeta(academic=academic),
    )
    organization_json = OrganizationJsonBuilder.json(
      organization, optimized_runs_in_billing_cycle=137, data_storage_bytes=10, total_runs_in_billing_cycle=138
    )
    assert set(organization_json.keys()) >= set(ORGANIZATION_FIELDS) | {"object"}
    assert organization_json["object"] == "organization"
    assert organization_json["id"] == str(organization.id)
    assert organization_json["name"] == organization.name
    assert organization_json["academic"] == organization.academic
    assert organization_json["optimized_runs_in_billing_cycle"] == 137
    assert organization_json["data_storage_bytes"] == 10
    assert organization_json["total_runs_in_billing_cycle"] == 138
