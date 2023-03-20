# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy
from scipy.stats import beta, gamma, halfcauchy, lognorm

from zigopt.assignments.build import set_assignments_map_from_dict
from zigopt.experiment.segmenter import ExperimentParameterSegmenter
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionData
from zigopt.suggestion.sampler.base import SuggestionSampler
from zigopt.suggestion.unprocessed.model import SuggestionDataProxy, UnprocessedSuggestion


REJECTION_SAMPLE_BLOCK_SIZE = 100
PROBABILITY_MASS_THRESHOLD = 0.25


def rejection_sample(sample_generator, lb, ub):
  samples = sample_generator(REJECTION_SAMPLE_BLOCK_SIZE)
  accepted_samples = samples[(lb <= samples) * (samples <= ub)]
  if len(accepted_samples) >= 1:
    return accepted_samples[0]
  return None


class PriorDistribution:
  def __init__(self, dist_family, dist_params, flip=False, has_log_transformation=False):
    self.distribution = dist_family(**dist_params)
    self.flip = flip
    self.has_log_transformation = has_log_transformation

  def sample(self, num_samples=1):
    samples = self.distribution.rvs(num_samples)
    if self.flip:
      samples = -samples
    if self.has_log_transformation:
      samples = 10**samples
    return samples

  def cdf(self, a):
    """
        NOTE: if log scaled, then returns CDF of log-scaled distribution (because the CDF of exp( prior) may not have a
        closed form)
        """
    if self.has_log_transformation:
      a = numpy.log10(a)
    if self.flip:
      return 1 - self.distribution.cdf(-a)
    else:
      return self.distribution.cdf(a)


class XGBSampler(SuggestionSampler):
  """
    For supported XGB parameters, this class allows one to sample according to that parameter using the metalearned
    distribution.
    """

  priors = {
    "eta": PriorDistribution(lognorm, dict(s=0.415, loc=-1.39, scale=2.616), flip=True, has_log_transformation=True),
    "gamma": PriorDistribution(
      halfcauchy,
      dict(loc=0, scale=0.827),
    ),
    "max_depth": PriorDistribution(
      gamma,
      dict(a=650.4, loc=-248.856, scale=0.41056),
    ),
    "min_child_weight": PriorDistribution(
      beta,
      dict(a=0.569, b=0.618, loc=1, scale=4.088),
    ),
    "max_delta_step": PriorDistribution(
      beta,
      dict(a=0.81, b=0.737, loc=-0.4, scale=10.4),
    ),
  }

  def __init__(self, services, experiment, optimization_args):
    super().__init__(services, experiment, None)
    self.source = UnprocessedSuggestion.Source.XGB
    self.active_priors = []
    self.check_active_priors()

  def sample_num_boost_round(self, param):
    """
        Samples from integers in [lb, ub] with probability equal to the values of said integers. Assumes that param
        is num_boost_round, which is the only situation in which this will get used
        """
    ub = param.bounds.maximum
    lb = param.bounds.minimum
    integers = numpy.arange(lb, ub + 1)
    probabilities = integers / numpy.sum(integers)
    return numpy.random.choice(integers, p=probabilities)

  def volume_in_range(self, param):
    ub = param.bounds.maximum
    lb = param.bounds.minimum
    if self.priors[param.name].has_log_transformation and lb <= 0:
      return 0
    return self.priors[param.name].cdf(ub) - self.priors[param.name].cdf(lb)

  def check_active_priors(self):
    """
        An active prior is one that has at least PROBABILITY_MASS_THRESHOLD percentage of it's probability mass within
        the user defined bounds
        """
    for param in [p for p in self.experiment.all_parameters if p.name in self.priors]:
      if self.volume_in_range(param) > PROBABILITY_MASS_THRESHOLD:
        self.active_priors.append(param.name)

  def has_active_prior(self, param):
    return param.name in self.active_priors

  def sample_from_prior(self, param):
    """
        Tries to sample from prior within bounds, using rejection sampling. If this fails, falls back to uniform random
        """
    if param.name == "num_boost_round":
      random_value = self.sample_num_boost_round(param)
    else:
      param_sampler = self.priors[param.name].sample
      random_value = rejection_sample(param_sampler, param.bounds.minimum, param.bounds.maximum)
      if random_value is None:
        random_value = numpy.random.uniform(param.bounds.minimum, param.bounds.maximum)
    if param.is_integer:
      random_value = int(random_value)
    return random_value

  def fetch_best_suggestions(self, limit):
    return self.generate_random_suggestions(limit)

  def generate_random_suggestions(self, count):
    return [self.form_unprocessed_suggestion(data=data) for data in self.generate_random_suggestion_datas(count)]

  def generate_random_suggestion_datas(self, count):
    suggestion_datas = self._generate_random_suggestion_datas(count)
    assert len(suggestion_datas) == count
    return suggestion_datas

  def _generate_random_suggestion_datas(self, count):
    ret = []
    for _ in range(count):
      suggestion_data = SuggestionData()
      suggestion_dict = dict()
      for param in self.experiment.all_parameters:
        if self.has_active_prior(param):
          random_value = self.sample_from_prior(param)
        else:
          random_value = ExperimentParameterSegmenter.random_value_for_parameter(param)
        suggestion_dict.update({param.name: random_value})
      set_assignments_map_from_dict(suggestion_data, suggestion_dict)
      ret.append(SuggestionDataProxy(suggestion_data))
    return ret
