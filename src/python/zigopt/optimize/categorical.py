# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *


@generator_to_safe_iterator
def _all_combos(list_of_lists):
  """Returns all possible ways to pick one element from each list, like ``itertools.product``."""
  if list_of_lists:
    these_possibilities = list_of_lists[0]
    sub_possibilities = _all_combos(list_of_lists[1:])
    for sub in sub_possibilities:
      for p in these_possibilities:
        yield [p] + sub
  else:
    yield []


def all_categorical_value_combos(categorical_parameters):
  """Produce all combinations (cartesian product) of categorical parameter values. Deleted categorical values
    are not included.

    :param categorical_parameters: parameter name & category enum indexes for categoricals of this experiment
    :type categorical_parameters: ``list`` of ``ExperimentParameter``
    :return: all combinations (cartesian product) of categorical values; each combo is
      *sorted* by parameter name
    :rtype: ``list`` of ``tuple`` of ``ObservationParam``
    """

  all_values_for_params = [
    [
      (parameter.name, categorical_value.enum_index)
      for categorical_value in parameter.all_categorical_values
      if not categorical_value.deleted
    ]
    for parameter in categorical_parameters
  ]

  categorical_values = _all_combos(all_values_for_params)
  return [frozenset(values) for values in categorical_values]
