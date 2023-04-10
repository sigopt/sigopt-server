# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest
from mock import Mock

from zigopt.experiment.model import Experiment
from zigopt.observation.model import Observation
from zigopt.suggestion.model import Suggestion
from zigopt.suggestion.processed.model import ProcessedSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class _TestSuggestionBase:
  @pytest.fixture(params=[True, False])
  def observation(self, request):
    if request.param:
      return Observation()
    return None

  @pytest.fixture
  def unprocessed(self, request):
    return UnprocessedSuggestion(
      id=3,
      experiment_id=5,
    )

  @pytest.fixture(params=[True, False])
  def processed(self, request):
    if request.param:
      return ProcessedSuggestion(
        experiment_id=5,
        suggestion_id=3,
      )
    return None

  @pytest.fixture
  def suggestion(self, processed, unprocessed, observation):
    return Suggestion(
      processed=processed,
      unprocessed=unprocessed,
      observation=observation,
    )

  @pytest.fixture
  def experiment(self):
    return Experiment(id=5)

  # pylint: disable=undefined-variable
  @pytest.mark.parametrize("attr", [attr for attr in dir(Suggestion) if not attr.startswith("__")])
  # pylint: enable=undefined-variable
  def test_suggestion_attr(self, attr, suggestion):
    getattr(suggestion, attr)


class TestSuggestionNullUnprocessed(_TestSuggestionBase):
  @pytest.fixture
  def suggestion(self, processed, unprocessed, observation):
    suggestion = Suggestion(
      processed=processed,
      unprocessed=unprocessed,
      observation=observation,
    )
    # pylint: disable=protected-access
    suggestion._unprocessed = None
    # pylint: enable=protected-access
    return suggestion

  def test_unprocessed_cannot_be_null(self, processed, observation):
    with pytest.raises(AssertionError):
      Suggestion(
        processed=processed,
        unprocessed=None,
        observation=observation,
      )

  def test_get_assignments(self, experiment, suggestion):
    with pytest.raises(AttributeError):
      suggestion.get_assignments(experiment)

  def test_get_assignment(self, suggestion):
    parameter = Mock()
    with pytest.raises(AttributeError):
      suggestion.get_assignment(parameter)

  def test_assignments(self, experiment, suggestion):
    with pytest.raises(AttributeError):
      suggestion.assignments(experiment)

  def test_get_conditional_assignments(self, experiment, suggestion):
    with pytest.raises(AttributeError):
      suggestion.get_conditional_assignments(experiment)


class TestSuggestion(_TestSuggestionBase):
  def test_get_assignments(self, experiment, suggestion):
    suggestion.get_assignments(experiment)

  def test_get_assignment(self, suggestion):
    parameter = Mock()
    suggestion.get_assignment(parameter)

  def test_assignments(self, experiment, suggestion):
    suggestion.assignments(experiment)

  def test_get_conditional_assignments(self, experiment, suggestion):
    suggestion.get_conditional_assignments(experiment)
