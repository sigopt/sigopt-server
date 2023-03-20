# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import itertools

import numpy

from zigopt.experiment.model import Experiment
from zigopt.net.errors import BadParamError
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_CATEGORICAL,
  ExperimentCategoricalValue,
  ExperimentParameter,
)


def convert_conditional_to_categorical_parameter(conditional):
  parameter = ExperimentParameter()
  parameter.name = conditional.name
  parameter.param_type = PARAMETER_CATEGORICAL
  parameter.all_categorical_values.extend(
    [ExperimentCategoricalValue(name=v.name, enum_index=v.enum_index) for v in conditional.values]
  )
  return parameter


def convert_to_unconditioned_experiment(experiment):
  conditionals = experiment.conditionals
  conditionals_as_cat_parameter_list = [convert_conditional_to_categorical_parameter(c) for c in conditionals]

  unconditioned_experiment_meta = experiment.experiment_meta.copy_protobuf()
  unconditioned_experiment_meta.ClearField("conditionals")
  for p in unconditioned_experiment_meta.all_parameters_unsorted:
    if p.conditions and not p.replacement_value_if_missing:
      if p.param_type == PARAMETER_CATEGORICAL:
        p.replacement_value_if_missing = p.all_categorical_values[-1].enum_index
      elif p.grid_values:
        p.replacement_value_if_missing = p.grid_values[-1]
      else:
        p.replacement_value_if_missing = p.bounds.maximum
  unconditioned_experiment_meta.all_parameters_unsorted.extend(conditionals_as_cat_parameter_list)
  unconditioned_experiment = Experiment(
    name=experiment.name,
    experiment_meta=unconditioned_experiment_meta,
    id=experiment.id,
    client_id=experiment.client_id,
    project_id=experiment.project_id,
  )
  return unconditioned_experiment


def check_all_conditional_values_satisfied(experiment_meta):
  num_conditional_values = numpy.product([len(c.values) for c in experiment_meta.conditionals])
  satisfied_parameter_configurations = set([])
  for parameter in experiment_meta.all_parameters_unsorted:
    conditional_values = []
    for conditional in experiment_meta.conditionals:
      parameter_conditions = {x.name: x.values for x in parameter.conditions}
      if conditional.name in parameter_conditions:
        conditional_values.append(parameter_conditions[conditional.name])
      else:  # If that conditional is not present for a parameter, then add all values
        conditional_values.append([x.enum_index for x in conditional.values])
    for selected_conditionals in itertools.product(*conditional_values):
      satisfied_parameter_configurations.add(selected_conditionals)

  if len(satisfied_parameter_configurations) != num_conditional_values:
    raise BadParamError("Need at least one parameter that satisfies each conditional value")
