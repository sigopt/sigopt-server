# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.assignments.build import set_assignments_map_with_conditionals_from_proxy
from zigopt.common.lists import coalesce
from zigopt.profile.timing import time_function
from zigopt.protobuf.gen.suggest.suggestion_pb2 import SuggestionMeta
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion


class OptimizationSource:
  """
    Base class for OptimizationSources. OptimizerService talks to multiple
    OptimizationSources and then collects their results and picks the best
    results among them.

    TODO(RTL-112): See if we can change this to also take in optimization_args ... probably could be done
    """

  def __init__(self, services, experiment):
    self.services = services
    self.experiment = experiment

  @property
  def hyperparameter_type(self):
    raise NotImplementedError()

  # Every source should have a unique name
  @property
  def name(self):
    raise NotImplementedError()

  def coalesce_num_to_suggest(self, limit=None):
    return coalesce(limit, self.services.config_broker.get("model.num_suggestions", default=5))

  def get_suggestions(self, optimization_args, limit=None):
    raise NotImplementedError()

  def get_hyperparameters(self, optimization_args):
    raise NotImplementedError()

  def should_execute_hyper_opt(self, num_successful_observations):
    raise NotImplementedError()

  def construct_initial_hyperparameters(self):
    raise NotImplementedError()

  @property
  def hyper_opt_dimension(self):
    raise NotImplementedError()

  @time_function(
    "sigopt.timing",
    log_attributes=lambda self, suggestions, optimization_args, *args, **kwargs: {
      "experiment": str(optimization_args.source.experiment.id),
    },
  )
  def get_scored_suggestions(self, suggestions, optimization_args, random_padding_suggestions):
    raise NotImplementedError()

  # TODO(RTL-113): Figure out the need for the proxies ... something to do with the conditionals ??
  def create_unprocessed_suggestions(self, suggestion_data_proxies, source_number):
    unprocessed_suggestion_list = []
    for proxy in suggestion_data_proxies:
      suggestion_data = proxy.copy_protobuf()
      set_assignments_map_with_conditionals_from_proxy(suggestion_data, proxy, self.experiment)
      suggestion_meta_kwargs = {"suggestion_data": suggestion_data}
      unprocessed_suggestion_list.append(
        UnprocessedSuggestion(
          experiment_id=self.experiment.id,
          source=source_number,
          suggestion_meta=SuggestionMeta(**suggestion_meta_kwargs),
        )
      )

    return unprocessed_suggestion_list

  # TODO(RTL-114): I do not even think this could be None anymore ... check it
  @staticmethod
  def extract_open_suggestion_datas(optimization_args):
    open_suggestion_datas = []
    if optimization_args.open_suggestions is not None:
      open_suggestion_datas = [s.suggestion_meta.suggestion_data for s in optimization_args.open_suggestions]
    return open_suggestion_datas

  # NOTE: The role of this function is to determine when we want to enqueue a hyper_opt call.
  #       We are placing it here to allow this to be called in a more coherent fashion.
  #
  # NOTE: We take num_observations here (not num_successful) because this is meant to lag calls based on
  #       a consistent frequency independently of whether the actual data is substantial.
  #
  # TODO(RTL-115): Maybe more naturally should be housed in ranker.py?
  #              Or, maybe some of what is in ranker.py more naturally belongs here?
  # TODO(RTL-116): Extend this concept to consider the importance computations
  # TODO(RTL-117): Should there be some consideration of parallel bandwidth here?
  def execute_gp_hyper_opt_call_based_on_lag(self, num_successful_observations):
    hyper_opt_dimension = self.hyper_opt_dimension

    # NOTE: Never allow hyper opt for larger problems until we handle the memory issues
    lag_matrix = [
      [1, 2, 3, 1000000, 1000000, 1000000],  # 1 <= dim < 11
      [2, 4, 6, 1000000, 1000000, 1000000],  # 11 <= dim < 21
      [1000000, 1000000, 1000000, 1000000, 1000000, 1000000],  # 21 <= dim < 26
      [1000000, 1000000, 1000000, 1000000, 1000000, 1000000],  # 26 <= dim < 31
      [1000000, 1000000, 1000000, 1000000, 1000000, 1000000],  # 31 <= dim < 36
      [1000000, 1000000, 1000000, 1000000, 1000000, 1000000],  # 36 <= dim < 41
    ]
    # 1      250       500      750     1000     1250     1500,  N bounds

    if hyper_opt_dimension < 11:
      dimension_index = 0
    elif 11 <= hyper_opt_dimension < 21:
      dimension_index = 1
    elif 21 <= hyper_opt_dimension < 26:
      dimension_index = 2
    elif 26 <= hyper_opt_dimension < 31:
      dimension_index = 3
    elif 31 <= hyper_opt_dimension < 36:
      dimension_index = 4
    elif 36 <= hyper_opt_dimension < 41:
      dimension_index = 5
    else:
      return False

    if num_successful_observations < 251:
      num_observed_index = 0
    elif 251 <= num_successful_observations < 501:
      num_observed_index = 1
    elif 501 <= num_successful_observations < 751:
      num_observed_index = 2
    elif 751 <= num_successful_observations < 1001:
      num_observed_index = 3
    elif 1001 <= num_successful_observations < 1251:
      num_observed_index = 4
    elif 1251 <= num_successful_observations < 1501:
      num_observed_index = 5
    else:
      return False

    lag = lag_matrix[dimension_index][num_observed_index]

    should_stagger_hyperopt = self.experiment.constraints
    if should_stagger_hyperopt:
      if hyper_opt_dimension < 5:
        lag = 1
      elif 5 <= hyper_opt_dimension < 10:
        lag = 4
      elif 10 <= hyper_opt_dimension < 15:
        lag = 8
      elif 15 <= hyper_opt_dimension < 20:
        lag = 12
      else:
        lag = hyper_opt_dimension
      if num_successful_observations < 200:
        lag = int(1.0 * lag)
      elif 200 <= num_successful_observations < 400:
        lag = int(1.5 * lag)
      elif 400 <= num_successful_observations < 600:
        lag = int(2.5 * lag)
      elif 600 <= num_successful_observations < 800:
        lag = int(4 * lag)
      else:
        return False

    return num_successful_observations % lag == 0
