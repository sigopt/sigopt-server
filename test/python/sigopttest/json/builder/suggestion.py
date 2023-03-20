# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.json.assignments import assignments_json
from zigopt.json.builder import SuggestionJsonBuilder
from zigopt.json.client_provided_data import client_provided_data_json

from sigopttest.json.builder.test_base import VISIBLE_SUGGESTION_FIELDS, BuilderTestBase


# TODO(SN-1006): should test CONDITIONAL_SUGGESTION_FIELDS
class TestsuggestionJsonBuilder(BuilderTestBase):
  @classmethod
  def check_visible_fields(cls, experiment, suggestion, suggestion_json):
    assert set(suggestion_json.keys()) >= set(VISIBLE_SUGGESTION_FIELDS) | {"object"}
    assert suggestion_json["object"] == "suggestion"
    assert suggestion_json["id"] == str(suggestion.id)
    assert suggestion_json["assignments"] == assignments_json(experiment, suggestion.get_assignments(experiment))
    assert suggestion_json["created"] == suggestion.created
    assert suggestion_json["deleted"] == suggestion.deleted
    assert suggestion_json["experiment"] == str(suggestion.experiment_id)
    assert suggestion_json["metadata"] == client_provided_data_json(suggestion.client_provided_data)
    assert suggestion_json["state"] == suggestion.state

  def test_visible_fields(self, experiment, suggestion, client_authorization):
    suggestion_json = SuggestionJsonBuilder.json(experiment, suggestion, client_authorization)
    self.check_visible_fields(experiment, suggestion, suggestion_json)
