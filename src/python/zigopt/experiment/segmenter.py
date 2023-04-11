# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import math

from zigopt.common import *
from zigopt.math.interval import RightOpenInterval
from zigopt.services.base import Service


class ExperimentParameterSegmenter(Service):
  """
    Segments experiment parameters into chunked ranges.

    For numerical parameters, this means splitting a range [0, 10] into chunks of a given size.
    For example, [0, 2], [2, 4], ..., [8, 10].

    For categorical parameters, this means splitting up values into disjoint sets of approximately
    equal size.
    """

  def segmented_intervals(self, parameter, sample_interval):
    if parameter.is_categorical:
      sorted_values = sorted([cv.enum_index for cv in parameter.active_categorical_values])
      split_points = [(i / sample_interval) * len(sorted_values) for i in range(sample_interval + 1)]
      endpoints = [(int(round(minimum)), int(round(maximum))) for minimum, maximum in sliding(split_points, 2)]
      return [frozenset(sorted_values[minimum:maximum]) for minimum, maximum in endpoints]
    if parameter.is_grid:
      sorted_values = sorted(parameter.grid_values)
      split_points = [(i / sample_interval) * len(sorted_values) for i in range(sample_interval + 1)]
      endpoints = [(int(round(minimum)), int(round(maximum))) for minimum, maximum in sliding(split_points, 2)]
      return [frozenset(sorted_values[minimum:maximum]) for minimum, maximum in endpoints]
    if not parameter.has_log_transformation:
      length = parameter.bounds.maximum - parameter.bounds.minimum

      def fencepost(i):
        return parameter.bounds.minimum + (i / sample_interval) * length

      intervals = [RightOpenInterval(fencepost(i), fencepost(i + 1)) for i in range(sample_interval)]
      intervals[-1] = intervals[-1].closure()
      return intervals
    log_min = math.log10(parameter.bounds.minimum)
    log_max = math.log10(parameter.bounds.maximum)
    length = log_max - log_min

    def fencepost(i):  # pylint: disable=function-redefined
      return log_min + (i / sample_interval) * length

    intervals = [RightOpenInterval(10 ** fencepost(i), 10 ** fencepost(i + 1)) for i in range(sample_interval)]
    intervals[-1] = intervals[-1].closure()
    return intervals

  def prune_intervals(self, experiment, with_assignments_maps, intervals):
    for has_assignments_map in with_assignments_maps:
      for name, assignment in has_assignments_map.get_assignments(experiment).items():
        remaining_intervals = intervals.get(name, [])
        to_remove = find(remaining_intervals, lambda i: assignment in i)  # pylint: disable=cell-var-from-loop
        if to_remove:
          remaining_intervals.remove(to_remove)

  def pick_value(self, parameter, intervals):
    if intervals:
      return self.sample_from_interval(parameter, non_crypto_random.choice(tuple(intervals)))
    return ExperimentParameterSegmenter.random_value_for_parameter(parameter)

  @staticmethod
  def random_value_for_parameter(param):
    # NOTE: Critical grid is first as grid can be also double/int type
    if param.is_grid:
      return non_crypto_random.choice(param.grid_values)
    if param.is_categorical:
      return non_crypto_random.choice([v.enum_index for v in param.active_categorical_values])
    if param.is_integer:
      return non_crypto_random.randint(round(param.bounds.minimum), round(param.bounds.maximum))
    if param.has_log_transformation:
      return 10 ** (non_crypto_random.uniform(math.log10(param.bounds.minimum), math.log10(param.bounds.maximum)))
    return non_crypto_random.uniform(param.bounds.minimum, param.bounds.maximum)

  def sample_from_interval(self, parameter, interval):
    if parameter.is_grid or parameter.is_categorical:
      return non_crypto_random.choice(tuple(interval))
    if parameter.is_double:
      return non_crypto_random.uniform(interval.min, interval.max)
    if parameter.is_integer:
      lb, ub = self.to_closed_integer_interval(interval)
      # NOTE: randint includes upper bound
      return non_crypto_random.randint(lb, ub)
    raise TypeError(f"Parameter: {parameter.name} unrecognized type")

  def to_closed_integer_interval(self, interval):
    lower_bound = int(math.ceil(interval.min))
    lower_bound = lower_bound if lower_bound in interval else lower_bound + 1
    upper_bound = int(math.floor(interval.max))
    upper_bound = upper_bound if upper_bound in interval else upper_bound - 1
    return (lower_bound, upper_bound)

  def has_values(self, parameter, interval):
    if parameter.is_integer and not parameter.is_grid:
      lb, ub = self.to_closed_integer_interval(interval)
      return lb <= ub
    return bool(interval)
