# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
  QUANTIZED_EXPERIMENT_PARAMETER_NAME,
)
from libsigopt.compute.domain import CategoricalDomain


def form_random_unconstrained_categorical_domain(dim, categoricals_allowed=True, quantized_allowed=True):
  domain_components = []
  for _ in range(dim):
    if numpy.random.random() < 0.1 and quantized_allowed:
      domain_components.append(
        {
          "var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME,
          "elements": list(sorted(numpy.random.choice(50, 4, replace=False) / 10 - 2.2)),
        }
      )
    elif numpy.random.random() < 0.25 and categoricals_allowed:
      domain_components.append(
        {"var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME, "elements": list(range(numpy.random.randint(2, 5)))}
      )
    elif numpy.random.random() < 0.5:
      bounds = [numpy.random.randint(-10, 0), numpy.random.randint(0, 10)]
      domain_components.append({"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": bounds})
    else:
      random_number = numpy.random.random()
      if random_number < 0.333:
        random_values = numpy.random.uniform(-2, 3, size=(2,))
      elif random_number < 0.666:
        random_values = numpy.random.gamma(0.3, 1.0, size=(2,))
      else:
        random_values = numpy.random.uniform(-34567, 12345, size=(2,))
      domain_components.append({"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": sorted(random_values)})
  return CategoricalDomain(domain_components)


def form_random_constrained_categorical_domain(n_double_param=5, n_int_param=5, n_cat_param=1, n_quantized_param=1):
  assert n_double_param >= 5
  assert n_int_param >= 5
  assert n_cat_param >= 1
  assert n_quantized_param >= 1
  dim = n_double_param + n_int_param + n_cat_param + n_quantized_param
  idx_shuffled = numpy.arange(dim)
  numpy.random.shuffle(idx_shuffled)
  idx_double = idx_shuffled[0:n_double_param]
  idx_int = idx_shuffled[n_double_param : n_double_param + n_int_param]
  idx_cat = idx_shuffled[n_double_param + n_int_param : n_double_param + n_int_param + n_cat_param]
  idx_quantized = idx_shuffled[n_double_param + n_int_param + n_cat_param :]

  # Form domain components
  domain_components = [None] * dim
  for i in idx_double:
    bounds = [0, numpy.random.randint(1, 5)]
    domain_components[i] = {"var_type": DOUBLE_EXPERIMENT_PARAMETER_NAME, "elements": bounds}
  for i in idx_int:
    bounds = [5, numpy.random.randint(10, 20)]
    domain_components[i] = {"var_type": INT_EXPERIMENT_PARAMETER_NAME, "elements": bounds}
  for i in idx_cat:
    domain_components[i] = {
      "var_type": CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
      "elements": list(range(numpy.random.randint(2, 5))),
    }
  for i in idx_quantized:
    domain_components[i] = {
      "var_type": QUANTIZED_EXPERIMENT_PARAMETER_NAME,
      "elements": list(sorted(numpy.random.choice(50, 4, replace=False) / 10 - 2.2)),
    }

  # Form constraints
  constraint_list = []
  constraint_weights_int = [0] * dim
  idx_constraint = numpy.random.choice(idx_int, 2, replace=False)
  for i in idx_constraint:
    constraint_weights_int[i] = -1
  constraint_list.append(
    {"weights": constraint_weights_int, "rhs": -18, "var_type": "int"},
  )

  constraint_weights_int = [0] * dim
  idx_constraint = numpy.random.choice(idx_int, 2, replace=False)
  for i in idx_constraint:
    constraint_weights_int[i] = 1
  constraint_list.append(
    {"weights": constraint_weights_int, "rhs": 12, "var_type": "int"},
  )

  constraint_weights_double = [0] * dim
  idx_constraint = numpy.random.choice(idx_double, 2, replace=False)
  for i in idx_constraint:
    constraint_weights_double[i] = -1
  constraint_list.append(
    {"weights": constraint_weights_double, "rhs": -1.5, "var_type": "double"},
  )

  constraint_weights_double = [0] * dim
  idx_constraint = numpy.random.choice(idx_double, 2, replace=False)
  for i in idx_constraint:
    constraint_weights_double[i] = 1
  constraint_list.append(
    {"weights": constraint_weights_double, "rhs": 0.5, "var_type": "double"},
  )

  return CategoricalDomain(domain_components, constraint_list)
