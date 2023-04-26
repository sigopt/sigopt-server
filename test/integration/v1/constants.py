# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from __future__ import annotations

from copy import deepcopy
from typing import Generic, Literal, TypeVar

from typing_extensions import NotRequired, TypedDict


class MetricMetaType(TypedDict):
  name: str
  objective: NotRequired[Literal["minimize"] | Literal["maximize"] | None]


class StoredMetricMetaType(MetricMetaType):
  strategy: Literal["store"]


class OptimizedMetricMetaType(MetricMetaType):
  threshold: NotRequired[float | None]
  strategy: NotRequired[Literal["optimize"] | None]


class ConstrainedMetricMetaType(MetricMetaType):
  threshold: float
  strategy: Literal["constraint"]


BoundType = TypeVar("BoundType", bound=int | float)


class BoundsMetaType(TypedDict, Generic[BoundType]):
  min: BoundType
  max: BoundType


class ParameterMetaType(TypedDict):
  name: str
  conditions: NotRequired[dict[str, str | list[str]] | None]


class NumericalParameterMetaType(ParameterMetaType):
  transformation: NotRequired[Literal["log"] | Literal["none"] | None]


class IntegerParameterMetaType(NumericalParameterMetaType):
  type: Literal["int"]


class BoundedIntegerParameterMetaType(IntegerParameterMetaType):
  bounds: BoundsMetaType[int]


class GriddedIntegerParameterMetaType(IntegerParameterMetaType):
  grid: list[int]


class ParameterPriorMetaType(TypedDict):
  name: str


class NormalParameterPriorMetaType(ParameterPriorMetaType):
  mean: float
  scale: float


class BetaParameterPriorMetaType(ParameterPriorMetaType):
  shape_a: float
  shape_b: float


class DoubleParameterMetaType(NumericalParameterMetaType):
  type: Literal["double"]
  prior: NotRequired[NormalParameterPriorMetaType | BetaParameterPriorMetaType | None]


class BoundedDoubleParameterMetaType(DoubleParameterMetaType):
  bounds: BoundsMetaType[float]


class GriddedDoubleParameterMetaType(DoubleParameterMetaType):
  grid: list[float]


class CategoricalValueMetaType(TypedDict):
  name: str


class CategoricalParameterMetaType(ParameterMetaType):
  type: Literal["categorical"]
  categorical_values: list[CategoricalValueMetaType | str]


AnyParameterMetaType = (
  BoundedIntegerParameterMetaType
  | GriddedIntegerParameterMetaType
  | BoundedDoubleParameterMetaType
  | GriddedDoubleParameterMetaType
  | CategoricalParameterMetaType
)


class ConditionalMeta(TypedDict):
  name: str
  values: list[str]


class LinearConstraintTermMeta(TypedDict):
  name: str
  weight: float


class LinearConstraintMeta(TypedDict):
  type: Literal["greater_than"] | Literal["less_than"]
  terms: list[LinearConstraintTermMeta]
  threshold: float


class TaskMeta(TypedDict):
  name: str
  cost: float


class BaseExperimentMetaType(TypedDict):
  type: NotRequired[str]
  name: NotRequired[str | None]
  parameters: list[AnyParameterMetaType]
  conditionals: NotRequired[list[ConditionalMeta] | None]
  num_solutions: NotRequired[int | None]
  linear_constraints: NotRequired[list[LinearConstraintMeta] | None]


AnyMetricMetaType = StoredMetricMetaType | OptimizedMetricMetaType | ConstrainedMetricMetaType


class CoreExperimentMetaType(BaseExperimentMetaType):
  metric: NotRequired[AnyMetricMetaType | None]
  metrics: NotRequired[list[AnyMetricMetaType] | None]
  observation_budget: NotRequired[int | None]
  project: NotRequired[str | None]
  tasks: NotRequired[list[TaskMeta]]


class AiExperimentMetaType(BaseExperimentMetaType):
  metrics: list[AnyMetricMetaType]
  budget: NotRequired[int | None]


DEFAULT_EXPERIMENT_META: CoreExperimentMetaType = dict(
  name="default experiment",
  metrics=[dict(name="profit")],
  observation_budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
  ],
)

DEFAULT_AI_EXPERIMENT_META: AiExperimentMetaType = dict(
  name="default ai experiment",
  metrics=[dict(name="profit")],
  budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
  ],
)

EXPERIMENT_META_CONDITIONALS: CoreExperimentMetaType = dict(
  name="conditional experiment",
  metrics=[dict(name="metric")],
  observation_budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0), conditions=dict(x=["5", "10"])),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")], conditions=dict(x="10")),
  ],
  conditionals=[
    dict(name="x", values=["1", "5", "10"]),
  ],
)

EXPERIMENT_META_MULTICONDITIONAL: CoreExperimentMetaType = dict(
  name="multiconditional experiment",
  metrics=[dict(name="metric")],
  observation_budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0), conditions=dict(x=["1", "5"])),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")], conditions=dict(x="5")),
  ],
  conditionals=[
    dict(name="x", values=["1", "5"]),
    dict(name="y", values=["1", "5"]),
    dict(name="z", values=["1", "5"]),
  ],
)

EXPERIMENT_META_MULTIMETRIC: CoreExperimentMetaType = dict(
  name="multimetric experiment",
  metrics=[dict(name="revenue"), dict(name="sales")],
  observation_budget=50,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
  ],
)

EXPERIMENT_META_MULTIMETRIC_MINIMIZED: CoreExperimentMetaType = deepcopy(EXPERIMENT_META_MULTIMETRIC)
EXPERIMENT_META_MULTIMETRIC_MINIMIZED["metrics"] = [
  dict(name="m1", objective="minimize"),
  dict(name="m2", objective="minimize"),
]

EXPERIMENT_META_MULTIMETRIC_THRESHOLD: CoreExperimentMetaType = deepcopy(EXPERIMENT_META_MULTIMETRIC)
EXPERIMENT_META_MULTIMETRIC_THRESHOLD["metrics"] = [
  dict(name="revenue", threshold=None),
  dict(name="sales", threshold=4.0),
]

EXPERIMENT_META_MULTISOLUTION: CoreExperimentMetaType = dict(
  name="multiopt experiment",
  metrics=[dict(name="profit")],
  observation_budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
  ],
  num_solutions=2,
)

EXPERIMENT_META_WITH_CONSTRAINTS: CoreExperimentMetaType = dict(
  name="default constrained experiment",
  metrics=[dict(name="profit")],
  observation_budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
    dict(name="f", type="double", bounds=dict(min=1, max=50)),
    dict(name="g", type="int", bounds=dict(min=1, max=50)),
  ],
  linear_constraints=[
    dict(
      type="greater_than",
      terms=[
        dict(name="f", weight=3.4234),
        dict(name="b", weight=3),
      ],
      threshold=4,
    ),
    dict(
      type="less_than",
      terms=[
        dict(name="f", weight=3),
        dict(name="b", weight=1.1),
      ],
      threshold=44,
    ),
    dict(
      type="greater_than",
      terms=[
        dict(name="a", weight=1),
        dict(name="g", weight=2),
      ],
      threshold=4,
    ),
    dict(
      type="less_than",
      terms=[
        dict(name="a", weight=1),
        dict(name="g", weight=2),
      ],
      threshold=64,
    ),
  ],
)

EXPERIMENT_META_MULTITASK: CoreExperimentMetaType = dict(
  name="multitask experiment",
  metrics=[dict(name="profit")],
  observation_budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
  ],
  tasks=[dict(name="cheapest", cost=0.1), dict(name="cheap", cost=0.5), dict(name="expensive", cost=1)],
)

EXPERIMENT_META_GRID: CoreExperimentMetaType = deepcopy(DEFAULT_EXPERIMENT_META)
EXPERIMENT_META_GRID["type"] = "grid"
EXPERIMENT_META_GRID["parameters"] = [
  dict(name="a", type="int", grid=[1, 2, 3, 4, 5]),
  dict(name="b", type="double", grid=[0.1, 0.2, 0.3]),
  dict(name="c", type="categorical", categorical_values=["a", "b", "c"]),
]
del EXPERIMENT_META_GRID["observation_budget"]

EXPERIMENT_META_SEARCH: CoreExperimentMetaType = dict(
  name="search experiment",
  metrics=[
    dict(name="constraint-1", strategy="constraint", threshold=2.1),
    dict(name="constraint-2", strategy="constraint", threshold=-5.2),
  ],
  observation_budget=50,
  parameters=[
    dict(name="a", type="double", bounds=dict(min=0, max=1)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
    dict(name="e", type="int", bounds=dict(min=1, max=50)),
  ],
)

ALL_META: dict[str, CoreExperimentMetaType] = dict(
  conditionals=EXPERIMENT_META_CONDITIONALS,
  constraints=EXPERIMENT_META_WITH_CONSTRAINTS,
  default=DEFAULT_EXPERIMENT_META,
  grid=EXPERIMENT_META_GRID,
  multimetric=EXPERIMENT_META_MULTIMETRIC,
  multisolution=EXPERIMENT_META_MULTISOLUTION,
  multitask=EXPERIMENT_META_MULTITASK,
  metric_threshold=EXPERIMENT_META_MULTIMETRIC_THRESHOLD,
  search=EXPERIMENT_META_SEARCH,
)
