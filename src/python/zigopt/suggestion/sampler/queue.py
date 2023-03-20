# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.profile.timing import *
from zigopt.redis.service import RedisServiceTimeoutError
from zigopt.suggestion.sampler.ranked import RankedSampler


class SuggestionQueueSampler(RankedSampler):
  # NOTE - The limit is NOT enforced here, intentionally, so as to give back all the points to be ranked
  @time_function(
    "sigopt.timing",
    log_attributes=lambda self, *args, **kwargs: {"experiment": str(self.experiment.id)},
  )
  def generate_suggestions(self, limit):
    try:
      return self.services.unprocessed_suggestion_service.get_suggestions_per_source(self.experiment)
    except RedisServiceTimeoutError as e:
      self.services.exception_logger.log_exception(
        e,
        extra={
          "function_name": "get_suggestions_per_source",
          "experiment_id": self.experiment.id,
        },
      )
    return []
