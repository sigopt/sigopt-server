# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from libsigopt.aux.constant import MINIMUM_VALUE_VAR
from libsigopt.compute.misc.constant import (
  CONSTANT_LIAR_MAX,
  CONSTANT_LIAR_MEAN,
  CONSTANT_LIAR_MIN,
  DEFAULT_CONSTANT_LIAR_VALUE,
)


DEFAULT_VALUE_VAR = 0.0
MIDPOINT_NORMALIZATION_SCALE_FACTOR = 0.1
MINIMUM_METRIC_HALF_WIDTH = 1.0e-8


class MetricMidpointInfo(object):
  def __init__(self):
    self.force_skip = False
    self.midpoint = self.scale = self.negate = None

  def __repr__(self):
    return f"{self.__class__.__name__}(mid={self.midpoint}, scale={self.scale}, skip={self.skip})"

  @property
  def skip(self):
    return self.force_skip or self.midpoint is None

  def get_negate_from_objective(self, objective):
    return 1 if objective == "minimize" else -1

  def compute_lie_value(self, lie_method):
    raise NotImplementedError()

  def relative_objective_value(self, values):
    if self.skip:
      return self.negate * values
    return self.negate * self.scale * (values - self.midpoint)

  def relative_objective_variance(self, value_vars):
    value_vars = value_vars if value_vars is not None else numpy.full_like(value_vars, DEFAULT_VALUE_VAR)
    if self.skip:
      return numpy.fmax(value_vars, 1e-6)  # Experimenting with MINIMUM_VALUE_VAR changes other things too
    return numpy.fmax(value_vars * self.scale**2, MINIMUM_VALUE_VAR)

  def undo_scaling(self, values):
    if self.skip:
      return self.negate * values
    return self.negate * values / self.scale + self.midpoint

  # NOTE: This will not reverse relative_objective_variance if the fmax were employed there
  def undo_scaling_variances(self, value_vars):
    if self.skip:
      return value_vars
    return value_vars / self.scale**2


class MultiMetricMidpointInfo(MetricMidpointInfo):
  def __init__(self, values, failures, objectives=None):
    """
        This is a wrapper for a list of SingleMetricMidpointInfo objects
        """
    super().__init__()

    assert len(numpy.asarray(values).shape) == 2, "values must be an n-D array"
    assert objectives is None or len(objectives) == values.shape[1], "there must be an objective for each metric"

    self.tuple_of_smmi = tuple(
      SingleMetricMidpointInfo(values=values[:, i], failures=failures, objective=objectives[i] if objectives else None)
      for i in range(values.shape[1])
    )

    self.negate = numpy.array([m.negate for m in self.tuple_of_smmi])
    self.midpoint = numpy.array([m.midpoint for m in self.tuple_of_smmi])
    self.scale = numpy.array([m.scale for m in self.tuple_of_smmi])
    self.force_skip = any(m.force_skip for m in self.tuple_of_smmi)
    # sync each SingleMetricMidpointInfo in case we need to access one of them
    if self.force_skip:
      for m in self.tuple_of_smmi:
        m.force_skip = True

  def compute_lie_value(self, lie_method):
    return numpy.array([m.compute_lie_value(lie_method) for m in self.tuple_of_smmi])


# NOTE: Probably should rename this if moving lie stuff in here
# NOTE: Any benefit to masked_arrays ??
class SingleMetricMidpointInfo(MetricMidpointInfo):
  def __init__(self, values, failures, objective=None):
    """Rescales the data from
          [min, max]
          to
          [MIDPOINT_NORMALIZATION_SCALE_FACTOR, -MIDPOINT_NORMALIZATION_SCALE_FACTOR]
          Note the application of the -1 that is applied, to convert a max problem to a min problem.

          This also now computes the "lie" or "failure" value, which I think makes sense because it's
          doing essentially the same computation

        """
    super().__init__()

    self.non_fail_values = values[numpy.logical_not(failures)]
    assert len(self.non_fail_values.shape) == 1, "values must be an 1-D array"

    self.negate = self.get_negate_from_objective(objective)

    if len(self.non_fail_values) == 0:
      self.force_skip = True

    if not self.force_skip:
      self.min, self.max = numpy.min(self.non_fail_values), numpy.max(self.non_fail_values)
      self.midpoint = (self.max + self.min) * 0.5

      if (self.max - self.min) * 0.5 < MINIMUM_METRIC_HALF_WIDTH:
        if min(numpy.abs([self.max, self.min])) > 1:
          self.scale = 1 / max(numpy.abs([self.min, self.max]))
          self.midpoint = self.min
        else:
          self.scale = 1
          self.midpoint = 0
      else:
        self.scale = 2 * MIDPOINT_NORMALIZATION_SCALE_FACTOR / (self.max - self.min)

  def compute_lie_value(self, lie_method):
    # TODO(RTL-56): Think about if, maybe, we should try/catch if this gets called with no non-failures
    if not len(self.non_fail_values):
      return DEFAULT_CONSTANT_LIAR_VALUE

    maximizing = bool(self.negate == -1)
    if lie_method == CONSTANT_LIAR_MIN:
      return numpy.min(self.non_fail_values) if maximizing else numpy.max(self.non_fail_values)
    elif lie_method == CONSTANT_LIAR_MAX:
      return numpy.max(self.non_fail_values) if maximizing else numpy.min(self.non_fail_values)
    elif lie_method == CONSTANT_LIAR_MEAN:
      return numpy.mean(self.non_fail_values)

    assert lie_method in (CONSTANT_LIAR_MAX, CONSTANT_LIAR_MIN, CONSTANT_LIAR_MEAN)
    return None


class HistoricalData(object):
  def __init__(self, dim):
    self.dim = dim
    self.points_sampled = numpy.empty((0, self.dim))
    self.points_sampled_value = numpy.empty(0)
    self.points_sampled_noise_variance = numpy.empty(0)

  def __str__(self):
    """String representation of this HistoricalData object."""
    return "\n".join(
      [repr(self.points_sampled), repr(self.points_sampled_value), repr(self.points_sampled_noise_variance)]
    )

  def append_lies(self, points_being_sampled, lie_value, lie_value_var):
    self.append_historical_data(
      numpy.asarray(points_being_sampled),
      lie_value * numpy.ones(len(points_being_sampled)),
      lie_value_var * numpy.ones(len(points_being_sampled)),
    )

  def append_historical_data(self, points_sampled, points_sampled_value, points_sampled_noise_variance):
    """Append lists of points_sampled, their values, and their noise variances to the data members of this class."""
    if points_sampled.size == 0:
      return

    assert len(points_sampled.shape) == 2
    assert len(points_sampled_value.shape) == len(points_sampled_noise_variance.shape) == 1
    assert len(points_sampled) == len(points_sampled_value) == len(points_sampled_noise_variance)
    assert points_sampled.shape[1] == self.dim

    self.points_sampled = numpy.append(self.points_sampled, points_sampled, axis=0)
    self.points_sampled_value = numpy.append(self.points_sampled_value, points_sampled_value)
    self.points_sampled_noise_variance = numpy.append(self.points_sampled_noise_variance, points_sampled_noise_variance)

  @property
  def num_sampled(self):
    """Return the number of sampled points."""
    return self.points_sampled.shape[0]
