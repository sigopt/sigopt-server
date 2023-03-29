# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from dataclasses import asdict

from zigopt.common import *
from zigopt.conditionals.util import convert_to_unconditioned_experiment
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData
from zigopt.sigoptcompute.adapter import SCAdapter
from zigopt.suggestion.sampler.base import SuggestionSampler
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from libsigopt.aux.domain import CategoricalDomain


# NOTE: This sampler should not be using the optimization_args at all, so I pass None in.
#       Probably could pass OptimizationArgs() to be more consistent, but this should be erroring
#       if there is ever any access to something that should not exist.
#       Could also copy from a different OptimizationArgs (if one exists) but this feel safer (in that we will
#       catch mistakes more quickly.
class RandomSampler(SuggestionSampler):
  def __init__(self, services, experiment, source):
    super().__init__(services, experiment, None)
    self.is_conditional = False
    if experiment.conditionals:
      self.experiment = convert_to_unconditioned_experiment(experiment)
      self._conditioned_experiment = experiment
      self.is_conditional = True
    self.source = source
    if self.source not in UnprocessedSuggestion.Source.get_random_sources():
      raise ValueError(f"Invalid source: {self.source}")

  def fetch_best_suggestions(self, limit):
    return self.generate_random_suggestions(limit)

  def generate_random_suggestions(self, count):
    if not self.is_conditional:
      return [self.form_unprocessed_suggestion(data=data) for data in self.generate_random_suggestion_datas(count)]

    unprocessed_suggestions = []
    for unconditioned_data in self.generate_random_suggestion_datas(count):
      conditioned_suggestion_data = SuggestionData(
        assignments_map=unconditioned_data.get_assignments(self._conditioned_experiment),
      )
      unprocessed_suggestions.append(self.form_unprocessed_suggestion(data=conditioned_suggestion_data))
    return unprocessed_suggestions

  # Note: right now if there are constraints we ignore the priors explicitly here. Down the road, we need to figure out
  # if we want to enable both (constraints on some params priors on others) and also if we want to do experiment-level
  # checking to see if there are both constraints and priors on the same param (which shouldn't be allowed)
  def generate_random_suggestion_datas(self, count):
    domain_info = SCAdapter.generate_domain_info(self.experiment, only_active_categorical_values=True)
    domain = CategoricalDomain(**asdict(domain_info))
    if domain_info.priors and not domain_info.constraint_list:
      samples = domain.generate_random_points_according_to_priors(count)
    else:
      samples = domain.generate_quasi_random_points_in_domain(count)
    # pylint: disable=protected-access
    suggestion_datas = SCAdapter._make_suggestion_datas(self.experiment, samples)
    # pylint: enable=protected-access
    assert len(suggestion_datas) == count
    return suggestion_datas

  @property
  def _default_task(self):
    return non_crypto_random.choice(self.experiment.tasks)
