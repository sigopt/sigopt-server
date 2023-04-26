# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from zigopt.optimize.sources.base import OptimizationSource
from zigopt.protobuf.gen.optimize.sources_pb2 import CategoricalHyperparameters, MultimetricHyperparameters
from zigopt.protobuf.lib import copy_protobuf
from zigopt.sigoptcompute.constant import (
  DEFAULT_AUTO_NOISE_ACTIVATED,
  DEFAULT_EI_WHEN_UNCOMPUTABLE,
  MINIMUM_INTEGER_LENGTH_SCALE,
  MINIMUM_SUCCESSES_TO_COMPUTE_EI,
)
from zigopt.suggestion.lib import ScoredSuggestion
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion

from libsigopt.aux.constant import (
  DEFAULT_HYPERPARAMETER_ALPHA,
  DEFAULT_HYPERPARAMETER_TASK_LENGTH_SCALE,
  DEFAULT_HYPERPARAMETER_TIKHONOV,
  DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS,
  DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS,
  DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS_WITH_CONSTRAINTS,
)


class CategoricalOptimizationSource(OptimizationSource):
  """
    This class exists specifically to allow for a single GP mechanism to work with mixed categorical/continuous
    experiments.  Maybe this could also handle pure categorical situations as well, but I'd imagine there is
    something better than this.

    The idea is that, for a categorical variable with k categories, k new continuous variables on [0, 1] are created.
    The category that is returned as a suggestion to SigOpt is chosen randomly with probably based on the values of the
    one_hot continuous dimensions.
    """

  name = "gp_categorical"

  def get_gp_cutoff_observation_count(self):
    return self.services.config_broker.get(
      "model.gp_cutoff_observation_count", DEFAULT_USE_SPE_AFTER_THIS_MANY_OBSERVATIONS
    )

  # This asks whether this optimization source is appropriate for the given experiment and num_observations
  def is_suitable_at_this_point(self, num_observations):
    max_dims = (
      DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS_WITH_CONSTRAINTS
      if len(self.experiment.constraints) > 0
      else DEFAULT_USE_SPE_BEYOND_THIS_MANY_DIMENSIONS
    )
    max_obs = self.get_gp_cutoff_observation_count()
    return self.hyper_opt_dimension < max_dims and num_observations < max_obs

  @property
  def hyperparameter_type(self):
    return MultimetricHyperparameters

  def should_execute_hyper_opt(self, num_successful_observations):
    return self.execute_gp_hyper_opt_call_based_on_lag(num_successful_observations)

  @property
  def hyper_opt_dimension(self):
    return sum(len(p.active_categorical_values) if p.is_categorical else 1 for p in self.experiment.all_parameters)

  @property
  def use_auto_noise(self):
    return DEFAULT_AUTO_NOISE_ACTIVATED

  def should_have_task_length(self):
    return self.experiment.is_multitask

  def construct_initial_hyperparameters(self):
    pass

  def default_hyperparameter_dict(self, optimization_args):
    mm_hyperparameter_dicts = []
    for _ in self.experiment.all_metrics:
      mm_hyperparameter_dicts.append(self.default_cat_hyperparameter_dict(optimization_args))
    return mm_hyperparameter_dicts

  def default_cat_hyperparameter_dict(self, optimization_args):
    should_have_task_length = self.should_have_task_length()
    return {
      "alpha": DEFAULT_HYPERPARAMETER_ALPHA,
      "length_scales": [[self._default_hyperparameter(p)] for p in self.experiment.all_parameters_sorted],
      "tikhonov": DEFAULT_HYPERPARAMETER_TIKHONOV if self.use_auto_noise else None,
      "task_length": DEFAULT_HYPERPARAMETER_TASK_LENGTH_SCALE if should_have_task_length else None,
    }

  @staticmethod
  def _default_hyperparameter(parameter):
    if parameter.is_categorical:
      return None

    if parameter.is_grid:
      return max(numpy.diff(parameter.grid_values))

    edge_length = parameter.bounds.maximum - parameter.bounds.minimum
    default = 0.1 * edge_length

    if parameter.is_integer:
      default = max(default, MINIMUM_INTEGER_LENGTH_SCALE)

    return default

  def should_force_default_hyperparameters(self, optimization_args, hyperparameters):
    if hyperparameters is None:  # Not even sure this could ever happen
      return True
    num_successful_points = optimization_args.observation_count - optimization_args.failure_count
    return num_successful_points <= 2 * self.hyper_opt_dimension

  def extract_hyperparameter_dict(self, optimization_args):
    multimetric_hyperparameter_dicts = []
    multimetric_hyperparameters = optimization_args.old_hyperparameters
    if multimetric_hyperparameters is None:
      return self.default_hyperparameter_dict(optimization_args)
    for hp in sorted(multimetric_hyperparameters.multimetric_hyperparameter_value, key=lambda val: val.metric_name):
      cat_hp_dict = self.extract_cat_hyperparameter_dict(optimization_args, hp.categorical_hyperparameters)
      multimetric_hyperparameter_dicts.append(cat_hp_dict)
    return multimetric_hyperparameter_dicts

  def extract_cat_hyperparameter_dict(self, optimization_args, hyperparameters):
    if self.should_force_default_hyperparameters(optimization_args, hyperparameters):
      return self.default_cat_hyperparameter_dict(optimization_args)
    return self._extract_cat_hyperparameter_dict(optimization_args, hyperparameters, self.use_auto_noise)

  # NOTE: Not sure how I feel about letting defaults exist in here ... consider in the future
  def _extract_cat_hyperparameter_dict(self, optimization_args, hyperparameters, use_auto_noise):
    length_scale_map = dict(((l.parameter_name, l.length_list) for l in hyperparameters.hyperparameter_lengths))

    alpha = (
      hyperparameters.hyperparameter_alpha
      if hyperparameters.HasField("hyperparameter_alpha")
      else DEFAULT_HYPERPARAMETER_ALPHA
    )

    length_scales = []
    for p in self.experiment.all_parameters_sorted:
      stored_lengths_list = length_scale_map.get(p.name)
      if not stored_lengths_list or (p.is_categorical and len(stored_lengths_list) != len(p.all_categorical_values)):
        stored_lengths_list = [self._default_hyperparameter(p)]
      length_scales.append(stored_lengths_list)

    tikhonov = None
    if use_auto_noise:
      tikhonov = (
        hyperparameters.hyperparameter_tikhonov
        if hyperparameters.HasField("hyperparameter_tikhonov")
        else DEFAULT_HYPERPARAMETER_TIKHONOV
      )

    task_length = None
    if self.should_have_task_length():
      task_length = (
        hyperparameters.task_length
        if hyperparameters.HasField("task_length")
        else DEFAULT_HYPERPARAMETER_TASK_LENGTH_SCALE
      )

    return {
      "alpha": alpha,
      "length_scales": length_scales,
      "tikhonov": tikhonov,
      "task_length": task_length,
    }

  def build_mm_hyperparameter_protobuf_from_dict(self, hyperparameter_dict):
    ret = MultimetricHyperparameters()
    for i, metric in enumerate(self.experiment.all_metrics):
      mmhpv = ret.multimetric_hyperparameter_value.add()
      mmhpv.metric_name = str(metric.name)
      mmhpv.categorical_hyperparameters.CopyFrom(
        copy_protobuf(self.build_cat_hyperparameter_protobuf_from_dict(hyperparameter_dict[i]))
      )
    return ret

  def build_cat_hyperparameter_protobuf_from_dict(self, hyperparameter_dict):
    ret = CategoricalHyperparameters()
    ret.hyperparameter_alpha = hyperparameter_dict["alpha"]
    for length_scales, parameter in zip(hyperparameter_dict["length_scales"], self.experiment.all_parameters_sorted):
      length = ret.hyperparameter_lengths.add()
      length.parameter_name = parameter.name
      if None not in length_scales:  # Provide no default values for categoricals
        length.length_list.extend(length_scales)
    if hyperparameter_dict["tikhonov"]:
      ret.hyperparameter_tikhonov = hyperparameter_dict["tikhonov"]
    if hyperparameter_dict["task_length"]:
      ret.task_length = hyperparameter_dict["task_length"]
    return ret

  def get_suggestions(self, optimization_args, limit=None):
    if optimization_args.observation_count - optimization_args.failure_count < MINIMUM_SUCCESSES_TO_COMPUTE_EI:
      return []

    # NOTE: limit metric constraint experiments to 1 suggestion, since it is using qEI for computation
    # Eventually, we want to up this to something > 1
    if self.experiment.has_constraint_metrics:
      limit = 1

    suggestion_datas = self.services.sc_adapter.gp_next_points_categorical(
      experiment=self.experiment,
      observations=list(optimization_args.observation_iterator),
      hyperparameter_dict=self.extract_hyperparameter_dict(optimization_args),
      num_to_suggest=self.coalesce_num_to_suggest(self.default_limit(limit)),
      open_suggestion_datas=self.extract_open_suggestion_datas(optimization_args),
    )

    return self.create_unprocessed_suggestions(
      suggestion_data_proxies=suggestion_datas,
      source_number=UnprocessedSuggestion.Source.GP_CATEGORICAL,
    )

  def default_limit(self, limit):
    if limit:
      return limit
    hyper_opt_dimension = self.hyper_opt_dimension
    if hyper_opt_dimension <= 10:
      return 5
    if hyper_opt_dimension <= 25:
      return 3
    if hyper_opt_dimension <= 35:
      return 2
    return 1

  def get_hyperparameters(self, optimization_args):
    """
        For this optimization source, the categorical hyperparameters are computed,
        stored and used in future computations.
        """
    if self.should_force_default_hyperparameters(optimization_args, optimization_args.old_hyperparameters):
      hyperparameter_dict = self.default_hyperparameter_dict(optimization_args)
    else:
      observations = list(optimization_args.observation_iterator)
      hyperparameter_dict = self.extract_hyperparameter_dict(optimization_args)
      if self.should_execute_hyper_opt(optimization_args.observation_count - optimization_args.failure_count):
        hyperparameter_dict = self.services.sc_adapter.gp_hyper_opt_categorical(
          experiment=self.experiment,
          observations=observations,
          old_hyperparameter_dict=hyperparameter_dict,
        )

    return self.build_mm_hyperparameter_protobuf_from_dict(hyperparameter_dict)

  def get_scored_suggestions(self, suggestions, optimization_args, random_padding_suggestions):
    all_suggestions = suggestions + random_padding_suggestions

    if optimization_args.observation_count - optimization_args.failure_count < MINIMUM_SUCCESSES_TO_COMPUTE_EI:
      return [ScoredSuggestion(s, DEFAULT_EI_WHEN_UNCOMPUTABLE) for s in all_suggestions]

    expected_improvements = self.services.sc_adapter.gp_ei_categorical(
      experiment=self.experiment,
      observations=list(optimization_args.observation_iterator),
      hyperparameter_dict=self.extract_hyperparameter_dict(optimization_args),
      suggestion_datas_to_evaluate=[s.suggestion_meta.suggestion_data for s in all_suggestions],
      open_suggestion_datas=self.extract_open_suggestion_datas(optimization_args),
    )

    return [ScoredSuggestion(suggestion, ei) for suggestion, ei in zip(all_suggestions, expected_improvements)]
