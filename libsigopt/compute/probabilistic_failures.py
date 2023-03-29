# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from dataclasses import dataclass

import numpy

from libsigopt.compute.predictor import HasPredictor, PredictorCoreComponents


POSITIVE_EXPONENT_CAP = 40.0
DEFAULT_KAPPA = 1


@dataclass(frozen=True, slots=True)
class FailureComponents:
  exponential: numpy.ndarray
  denominator: numpy.ndarray
  core_components: PredictorCoreComponents


@dataclass(frozen=True, slots=True)
class FailureListProductComponents:
  poss: numpy.ndarray
  grad_poss: numpy.ndarray


class ProbabilisticFailuresBase(object):
  @property
  def info_for_logs(self):
    raise NotImplementedError()

  def verify_points_to_evaluate(self, points_to_evaluate):
    eval_shape = points_to_evaluate.shape
    assert len(eval_shape) == 2
    assert eval_shape[1] == self.dim, f"dim of point: {eval_shape[1]} != dim of the model: {self.dim}"

  @property
  def dim(self):
    raise NotImplementedError()

  def __len__(self):
    raise NotImplementedError()

  @property
  def points_sampled(self):
    raise NotImplementedError()

  def compute_failure_components(self, points_to_evaluate, option):
    raise NotImplementedError()

  def compute_probability_of_success(self, points_to_evaluate):
    self.verify_points_to_evaluate(points_to_evaluate)
    return self._compute_probability_of_success(self.compute_failure_components(points_to_evaluate, "func"))

  def _compute_probability_of_success(self, failure_components):
    raise NotImplementedError()

  def compute_grad_probability_of_success(self, points_to_evaluate):
    self.verify_points_to_evaluate(points_to_evaluate)
    return self._compute_grad_probability_of_success(self.compute_failure_components(points_to_evaluate, "grad"))

  def _compute_grad_probability_of_success(self, failure_components):
    raise NotImplementedError()

  def joint_function_gradient_eval(self, points_to_evaluate):
    self.verify_points_to_evaluate(points_to_evaluate)
    failure_components = self.compute_failure_components(points_to_evaluate, "both")
    pos = self._compute_probability_of_success(failure_components)
    pos_grad = self._compute_grad_probability_of_success(failure_components)
    return pos, pos_grad


class ProbabilisticFailures(HasPredictor, ProbabilisticFailuresBase):
  def __init__(self, predictor, threshold):
    super().__init__(predictor)
    assert threshold is not None
    assert not numpy.isnan(threshold)
    self.threshold = threshold
    points_sampled_values_range = numpy.ptp(self.predictor.points_sampled_value)
    if points_sampled_values_range == 0:
      self.kappa = DEFAULT_KAPPA
    else:
      self.kappa = numpy.log(9) / (0.1 * points_sampled_values_range)

  def __repr__(self):
    return f"Logistic function: (1.0 + exp({self.kappa} * (mu(x) - {self.threshold})))^-1"

  def __len__(self):
    return 1

  @property
  def info_for_logs(self):
    return {
      "threshold": self.threshold,
      "num_points": self.predictor.num_sampled,
      "num_points_beyond_threshold": sum(self.predictor.points_sampled_value < self.threshold),
    }

  # We upper bound the exponent for numerical stability
  def compute_failure_components(self, points_to_evaluate, option):
    self.verify_points_to_evaluate(points_to_evaluate)
    core_components = self.compute_core_components(points_to_evaluate, option)
    exponential = numpy.exp(numpy.fmin(self.kappa * (core_components.mean - self.threshold), POSITIVE_EXPONENT_CAP))
    denominator = 1 + exponential
    return FailureComponents(exponential, denominator, core_components)

  def _compute_probability_of_success(self, failure_components):
    assert isinstance(failure_components, FailureComponents)
    return 1 / failure_components.denominator

  def _compute_grad_probability_of_success(self, failure_components):
    assert isinstance(failure_components, FailureComponents)
    if failure_components.core_components.grad_mean is None:
      return None
    chain_rule = -self.kappa * failure_components.exponential / failure_components.denominator**2
    return chain_rule[:, None] * failure_components.core_components.grad_mean


# Use Probability of Improvement style computation for ProbabilisticFailure
class ProbabilisticFailuresCDF(HasPredictor, ProbabilisticFailuresBase):
  def __init__(self, predictor, threshold):
    super().__init__(predictor)
    assert threshold is not None
    assert not numpy.isnan(threshold)
    self.threshold = threshold
    # NOTE: setting self.best_value to the threshold allows to leverage the computation
    # of core_compoments in HasPredictor
    self.best_value = self.threshold

  def __repr__(self):
    return f"norm.cdf(({self.threshold} - mu(x)) / std(x))"

  def __len__(self):
    return 1

  @property
  def info_for_logs(self):
    return {
      "threshold": self.threshold,
      "num_points": self.predictor.num_sampled,
      "num_points_beyond_threshold": sum(self.predictor.points_sampled_value < self.threshold),
    }

  def compute_failure_components(self, points_to_evaluate, option):
    self.verify_points_to_evaluate(points_to_evaluate)
    core_components = self.compute_core_components(points_to_evaluate, option)
    return FailureComponents(0, 0, core_components)

  def _compute_probability_of_success(self, failure_components):
    assert isinstance(failure_components, FailureComponents)
    return failure_components.core_components.cdf_z

  def _compute_grad_probability_of_success(self, failure_components):
    assert isinstance(failure_components, FailureComponents)
    cc = failure_components.core_components
    return -(cc.pdf_z / cc.sqrt_var)[:, None] * (cc.grad_mean + cc.z[:, None] * cc.grad_sqrt_var)


class ProductOfListOfProbabilisticFailures(ProbabilisticFailuresBase):
  def __init__(self, list_of_probabilistic_failures):
    assert len(list_of_probabilistic_failures) >= 1
    dim = list_of_probabilistic_failures[0].dim
    for pf in list_of_probabilistic_failures:
      assert isinstance(pf, ProbabilisticFailuresBase)
      assert pf.dim == dim
    self.list_of_probabilistic_failures = list_of_probabilistic_failures
    self.num_pfs = len(self.list_of_probabilistic_failures)

  def __repr__(self):
    return f"Product of {self.list_of_probabilistic_failures}"

  def __len__(self):
    return len(self.list_of_probabilistic_failures)

  @property
  def info_for_logs(self):
    return {f"failure_model_{i}: {pf.info_for_logs}" for i, pf in enumerate(self.list_of_probabilistic_failures)}

  @property
  def dim(self):
    return self.list_of_probabilistic_failures[0].dim

  @property
  def differentiable(self):
    return all(pf.differentiable for pf in self.list_of_probabilistic_failures)

  @property
  def points_sampled(self):
    return self.list_of_probabilistic_failures[0].predictor.points_sampled

  def compute_failure_components(self, points_to_evaluate, option):
    poss = grad_poss = None
    if option in ("func",):
      poss = numpy.zeros((self.num_pfs, len(points_to_evaluate)))
      for i, pf in enumerate(self.list_of_probabilistic_failures):
        poss[i] = pf.compute_probability_of_success(points_to_evaluate)
    if option in ("grad", "both"):
      poss = numpy.zeros((self.num_pfs, len(points_to_evaluate)))
      grad_poss = numpy.zeros((self.num_pfs, len(points_to_evaluate), self.dim))
      for i, pf in enumerate(self.list_of_probabilistic_failures):
        poss[i], grad_poss[i] = pf.joint_function_gradient_eval(points_to_evaluate)
    return FailureListProductComponents(poss, grad_poss)

  def _compute_probability_of_success(self, failure_components):
    assert isinstance(failure_components, FailureListProductComponents)
    return numpy.product(failure_components.poss, axis=0)

  def _compute_grad_probability_of_success(self, failure_components):
    assert isinstance(failure_components, FailureListProductComponents)
    poss = failure_components.poss
    grad_poss = failure_components.grad_poss
    grad = numpy.zeros(grad_poss[0].shape)
    for i in range(self.num_pfs):
      mask_array = numpy.ones(self.num_pfs, dtype=bool)
      mask_array[i] = False
      grad += grad_poss[i] * numpy.product(poss[mask_array], axis=0)[:, None]
    return grad
