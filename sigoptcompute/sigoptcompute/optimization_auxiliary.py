# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from dataclasses import asdict, dataclass

import numpy


class Optimizer(object):
  def optimize(self, **kwargs):
    raise NotImplementedError()


@dataclass(frozen=True, slots=True)
class OptimizerInfo:
  optimizer: type[Optimizer]
  parameters: object
  num_multistarts: int
  num_random_samples: int


@dataclass(frozen=True, slots=True)
class OptimizationResults:
  starting_points: numpy.ndarray
  ending_points: numpy.ndarray
  function_values: numpy.ndarray


####
#  VECTORIZED OPTIMIZATION PARAMETER OBJECTS
####


@dataclass(frozen=True, slots=True)
class AdamParameters:
  beta_1: float = 0.9
  beta_2: float = 0.9
  epsilon: float = 1e-8
  learning_rate: float = 0.01


@dataclass(frozen=True, slots=True)
class DEParameters:
  crossover_probability: float = 0.7
  mutation: float = 0.8
  strategy: str = "best1bin"


####
#  SCIPY OPTIMIZATION PARAMETER OBJECTS
####


@dataclass(frozen=True, slots=True)
class LBFGSBParameters:
  approx_grad: bool = False  # if true, BFGS will approximate the gradient
  maxfun: int = 15000  # maximum number of objective function calls to make
  maxcor: int = 10  # maximum number of variable metric corrections
  ftol: float = 1.0e-4  # iterate until (f^k - f^{k+1})/max{|f^k|,|f^{k+1}|,1} <= ftol
  gtol: float = 1.0e-4  # cutoff for highest component of gradient to be a critical point
  eps: float = 1.0e-8  # step size for approximating the gradient

  def scipy_kwargs(self) -> dict:
    return asdict(self)


@dataclass(frozen=True, slots=True)
class SLSQPParameters:
  approx_grad: bool = False  # use a finite difference gradient approximation
  maxiter: int = 150  # maximum number of SLSQP iterations to take
  ftol: float = 1.0e-4  # relative error for function value for convergence
  eps: float = 1.0e-8  # finite difference parameter if approx_grad == True

  def scipy_kwargs(self) -> dict:
    return asdict(self)


DEFAULT_VECOPT_MAXITER = 100
DEFAULT_ADAM_PARAMETERS = AdamParameters()
DEFAULT_DE_PARAMETERS = DEParameters()
DEFAULT_LBFGSB_PARAMETERS = LBFGSBParameters()
DEFAULT_SLSQP_PARAMETERS = SLSQPParameters()

OPTIMIZATION_PARAMETERS_TO_DEFAULTS = {
  AdamParameters: DEFAULT_ADAM_PARAMETERS,
  DEParameters: DEFAULT_DE_PARAMETERS,
  LBFGSBParameters: DEFAULT_LBFGSB_PARAMETERS,
  SLSQPParameters: DEFAULT_SLSQP_PARAMETERS,
}
