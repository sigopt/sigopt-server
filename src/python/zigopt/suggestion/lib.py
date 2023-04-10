# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class ScoredSuggestion:
  def __init__(self, suggestion, score):
    assert isinstance(suggestion, UnprocessedSuggestion)
    self.suggestion = suggestion
    self.score = score

  def __repr__(self):
    return f"ScoredSuggestion(suggestion_id={self.suggestion and self.suggestion.id}, score={self.score})"


class SuggestionException(Exception):
  pass


class SuggestionAlreadyProcessedError(SuggestionException):
  def __init__(self, processed_suggestion):
    super().__init__(
      f"Race condition processing suggestion {processed_suggestion.suggestion_id}"
      f" for experiment {processed_suggestion.experiment_id}."
    )
    self.suggestion_id = processed_suggestion.suggestion_id
    self.experiment_id = processed_suggestion.experiment_id
    self.queued_id = processed_suggestion.queued_id


class CouldNotProcessSuggestionError(SuggestionException):
  def __init__(self):
    super().__init__("We are unable to generate a suggestion for your experiment at this time")


class DuplicateUnprocessedSuggestionError(SuggestionException):
  pass
