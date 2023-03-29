# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.common import *
from zigopt.experiment.constant import (  # type: ignore
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  EXPERIMENT_PARAMETER_TYPE_TO_NAME,
  PARAMETER_TRANSFORMATION_TYPE_TO_NAME,
)
from zigopt.json.builder.json_builder import JsonBuilder, JsonBuilderValidationType, ValidationType, field
from zigopt.json.conditions import conditions_json
from zigopt.json.render import render_param_value
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (  # type: ignore
  Bounds,
  ExperimentCategoricalValue,
  ExperimentParameter,
  Prior,
)

from libsigopt.aux.constant import ParameterPriorNames  # type: ignore


class BoundsJsonBuilder(JsonBuilder):
  object_name = "bounds"

  def __init__(self, bounds: Bounds):
    self._bounds = bounds

  @field(ValidationType.number)
  def min(self) -> float:
    return self._bounds.minimum

  @field(ValidationType.number)
  def max(self) -> float:
    return self._bounds.maximum


class BasePriorJsonBuilder(JsonBuilder):
  PARAMETER_PRIOR_NAME: str

  def __init__(self, prior: Prior):
    self._prior = prior

  @field(ValidationType.string)
  def name(self) -> str:
    return self.PARAMETER_PRIOR_NAME


class NormalPriorJsonBuilder(BasePriorJsonBuilder):
  object_name = "normal_prior"

  PARAMETER_PRIOR_NAME = ParameterPriorNames.NORMAL

  @field(ValidationType.number)
  def mean(self) -> float:
    return self._prior.mean

  @field(ValidationType.number)
  def scale(self) -> float:
    return self._prior.scale


class BetaPriorJsonBuilder(BasePriorJsonBuilder):
  object_name = "beta_prior"

  PARAMETER_PRIOR_NAME = ParameterPriorNames.BETA

  @field(ValidationType.number)
  def shape_a(self) -> float:
    return self._prior.shape_a

  @field(ValidationType.number)
  def shape_b(self) -> float:
    return self._prior.shape_b


class CategoricalValueJsonBuilder(JsonBuilder):
  object_name = "categorical_value"

  def __init__(self, categorical_value: ExperimentCategoricalValue):
    self._categorical_value = categorical_value

  @field(ValidationType.string)
  def name(self) -> str:
    return self._categorical_value.name

  @field(ValidationType.integer)
  def enum_index(self) -> int:
    return self._categorical_value.enum_index


class ExperimentParameterJsonBuilder(JsonBuilder):
  object_name = "parameter"

  def __init__(self, param, experiment):
    self._param = param
    self._experiment = experiment

  @field(ValidationType.string)
  def name(self) -> str:
    return self._param.name

  @field(ValidationType.string)
  def type(self) -> Optional[str]:
    return napply(self._param.param_type, EXPERIMENT_PARAMETER_TYPE_TO_NAME.get)

  @field(ValidationType.arrayOf(JsonBuilderValidationType()))
  def categorical_values(self) -> Optional[list[CategoricalValueJsonBuilder]]:
    return (
      [
        CategoricalValueJsonBuilder(v)
        for v in sorted(self._param.active_categorical_values, key=lambda v: v.enum_index)
      ]
      if self._param.is_categorical
      else None
    )

  @field(JsonBuilderValidationType())
  def prior(self) -> Optional[BasePriorJsonBuilder]:
    if self._param.GetFieldOrNone("prior") is not None:
      type_to_builder = {
        Prior.NORMAL: lambda p: NormalPriorJsonBuilder(p.normal_prior),
        Prior.BETA: lambda p: BetaPriorJsonBuilder(p.beta_prior),
      }
      # TODO(SN-988): we probably want to know if we can't find a builder
      # should this raise a soft exception?
      builder = type_to_builder.get(self._param.prior.GetFieldOrNone("prior_type"))
      if builder:
        return builder(self._param.prior)
    return None

  @field(ValidationType.objectOf(ValidationType.array))
  def conditions(self) -> dict[str, list[str]]:
    return conditions_json(self._param.conditions, self._experiment)

  @field(JsonBuilderValidationType())
  def bounds(self) -> Optional[BoundsJsonBuilder]:
    return napply(self._param.GetFieldOrNone("bounds"), BoundsJsonBuilder)

  @field(ValidationType.assignment)
  def default_value(self) -> Optional[int | float | str]:
    return napply(  # type: ignore
      self._param.GetFieldOrNone("replacement_value_if_missing"), lambda rep: render_param_value(self._param, rep)
    )

  def hide_grid(self):
    return not self._param.grid_values

  @field(ValidationType.arrayOf(ValidationType.assignment), hide=hide_grid)
  def grid(self) -> list[int | float | str]:
    return [render_param_value(self._param, assignment) for assignment in self._param.grid_values]

  @field(ValidationType.string)
  def transformation(self) -> Optional[str]:
    if self.type() != DOUBLE_EXPERIMENT_PARAMETER_NAME:
      return None
    # NOTE: we special case to not return the string "none", which may be confusing
    if self._param.transformation == ExperimentParameter.TRANSFORMATION_NONE:
      return None
    return PARAMETER_TRANSFORMATION_TYPE_TO_NAME[self._param.transformation]
