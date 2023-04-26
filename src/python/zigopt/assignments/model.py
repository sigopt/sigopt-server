# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from zigopt.common import *
from zigopt.handlers.validate.assignments import parameter_conditions_satisfied
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import ExperimentParameter
from zigopt.protobuf.lib import copy_protobuf
from zigopt.protobuf.proxy import Proxy


class MissingValueException(Exception):
  pass


def make_experiment_assignment_value_array(has_assignments, parameters, vals=None, log_scale=False):
  # TODO(SN-1069): This copy_protobuf was added for performance in the presence of
  # immutable protobufs. Is it still necessary?
  has_assignments = copy_protobuf(has_assignments)
  values_dict = has_assignments.assignments_map
  for parameter in parameters:
    if parameter.name not in values_dict:
      if parameter.HasField("replacement_value_if_missing"):
        values_dict[parameter.name] = parameter.replacement_value_if_missing
  vals = coalesce(vals, numpy.empty(len(parameters)))
  for j, parameter in enumerate(parameters):
    try:
      if log_scale and parameter.transformation == ExperimentParameter.TRANSFORMATION_LOG:
        vals[j] = numpy.log10(values_dict[parameter.name])
      else:
        vals[j] = values_dict[parameter.name]
    except KeyError as e:
      raise MissingValueException("Missing value in has_assignments object") from e
  return vals


def extract_array_for_computation_from_assignments(has_assignments, parameters, vals):
  return make_experiment_assignment_value_array(has_assignments, parameters, vals=vals, log_scale=True)


class HasAssignmentsMap(Proxy):
  @property
  def assignments_map(self):
    raise Exception("Do not access .assignments_map directly - prefer .get_assignments(experiment)")

  def _get_required_parameter(self, array, parameter, index):
    ret = array[index]
    if ret is None:
      raise ValueError(f"Parameter has no replacement value: {parameter.name}")
    return ret

  def _get_assignments_as_value_array(self, parameters):
    """
        Returns this object as an array of assignment values, one for each parameter,
        in the same order as the provided list of parameters
        """
    return make_experiment_assignment_value_array(self, parameters)

  def get_assignment(self, parameter):
    if parameter.deleted:
      return None
    return self._get_required_parameter(self._get_assignments_as_value_array([parameter]), parameter, 0)

  def get_assignments(self, experiment):
    parameters = experiment.all_parameters
    conditionals = list(experiment.conditionals)
    values = self._get_assignments_as_value_array(parameters + conditionals)
    values_as_map = dict((p.name, v) for (p, v) in zip(parameters + conditionals, values))
    assignments = dict(
      (p.name, self._get_required_parameter(values, p, i))
      for (i, p) in enumerate(parameters)
      if parameter_conditions_satisfied(p, values_as_map)
    )
    if experiment.conditionals:
      # TODO(SN-1070): This calls make_experiment_assignment_value_array again redundantly, which
      # could be more efficient.
      assignments.update(self.get_conditional_assignments(experiment))
    return remove_nones_mapping(assignments)

  def get_conditional_assignments(self, experiment):
    conditional_values = self._get_assignments_as_value_array(experiment.conditionals)
    return dict((c.name, value) for (c, value) in zip(experiment.conditionals, conditional_values))
