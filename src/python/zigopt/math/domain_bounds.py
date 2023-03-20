# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import numpy

from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import PARAMETER_CATEGORICAL, PARAMETER_INT


def get_parameter_domain_bounds(parameter_list):
  domain_bounds = []
  for parameter in parameter_list:
    if parameter.param_type == PARAMETER_CATEGORICAL:
      domain_bounds.append([0, 1])
    elif parameter.param_type == PARAMETER_INT:
      domain_bounds.append([parameter.bounds.minimum - 0.49, parameter.bounds.maximum + 0.49])
    else:
      domain_bounds.append([parameter.bounds.minimum, parameter.bounds.maximum])
  return numpy.array(domain_bounds)
