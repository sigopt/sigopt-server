# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import math

from libsigopt.aux.constant import MINIMUM_VALUE_VAR

from zigopt.profile.timing import *
from zigopt.services.base import Service


class SuggestionRanker(Service):
  @time_function(
    "sigopt.timing",
    log_attributes=lambda self, suggestions, optimization_args, *args, **kwargs: {
      "experiment": str(optimization_args.source.experiment.id),
    },
  )
  def get_ranked_suggestions_excluding_low_score(self, suggestions, optimization_args, random_padding_suggestions):
    """
        Returns a list of the best suggestions ordered in decreasing order, with the 0th index as the best suggestion
        """
    if not suggestions + random_padding_suggestions:
      return []

    scored_suggestions = optimization_args.source.get_scored_suggestions(
      suggestions,
      optimization_args,
      random_padding_suggestions,
    )
    ranked_suggestions = sorted(scored_suggestions, key=lambda x: x.score, reverse=True)
    cutoff_index = find_index(ranked_suggestions, lambda x: x.score <= math.sqrt(MINIMUM_VALUE_VAR))
    return [rs.suggestion for rs in ranked_suggestions[:cutoff_index]]
