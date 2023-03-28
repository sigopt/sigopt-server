# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from libsigopt.aux.constant import (
  CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  DOUBLE_EXPERIMENT_PARAMETER_NAME,
  INT_EXPERIMENT_PARAMETER_NAME,
)


TEST_PROB_FAILED_OBSERVATION = 0.1

PARAMETER_DOUBLE = dict(
  name="d1",
  type=DOUBLE_EXPERIMENT_PARAMETER_NAME,
  bounds=dict(min=0, max=10),
)

PARAMETER_DOUBLE_LOG = dict(
  name="l1",
  type=DOUBLE_EXPERIMENT_PARAMETER_NAME,
  bounds=dict(min=1e-5, max=1),
  transformation="log",
)

PARAMETER_INT = dict(
  name="i1",
  type=INT_EXPERIMENT_PARAMETER_NAME,
  bounds=dict(min=10, max=20),
)

PARAMETER_CATEGORICAL = dict(
  name="c1",
  type=CATEGORICAL_EXPERIMENT_PARAMETER_NAME,
  categorical_values=["a", "b", "c"],
)

PARAMETER_GRID = dict(name="g1", type=DOUBLE_EXPERIMENT_PARAMETER_NAME, grid=[0.01, 0.1, 0.3, 0.9])

PARAMETER_NORMAL_PRIOR = dict(
  name="parameter_normal",
  type=DOUBLE_EXPERIMENT_PARAMETER_NAME,
  bounds=dict(min=0, max=10),
  prior=dict(name="normal", mean=5, scale=2),
)

PARAMETER_BETA_PRIOR = dict(
  name="parameter_beta",
  type=DOUBLE_EXPERIMENT_PARAMETER_NAME,
  bounds=dict(min=0, max=1),
  prior=dict(name="beta", shape_a=1, shape_b=10),
)

DEFAULT_PARAMETERS = [
  PARAMETER_DOUBLE,
  PARAMETER_DOUBLE_LOG,
  PARAMETER_INT,
  PARAMETER_CATEGORICAL,
  PARAMETER_GRID,
]

DEFAULT_PARAMETER_WITH_PRIORS = [
  PARAMETER_NORMAL_PRIOR,
  PARAMETER_CATEGORICAL,
  PARAMETER_BETA_PRIOR,
]

DEFAULT_SIMPLE_PARAMETERS = [
  PARAMETER_DOUBLE,
  PARAMETER_INT,
]

DEFAULT_METRICS = [
  dict(name="y1", objective="maximize", strategy="optimize"),
]

DEFAULT_METRICS_MULTIPLE = [
  dict(name="y1", objective="maximize", strategy="optimize"),
  dict(name="y2", objective="minimize", strategy="optimize"),
]

DEFAULT_METRICS_THRESHOLDS = [
  dict(
    name="y1",
    objective="maximize",
    strategy="optimize",
    threshold=0.5,
  ),
  dict(
    name="y2",
    objective="minimize",
    strategy="optimize",
  ),
]

DEFAULT_METRICS_ONE_CONSTRAINT = [
  dict(
    name="y1",
    objective="maximize",
    strategy="constraint",
    threshold=0.5,
  ),
  dict(
    name="y2",
    objective="minimize",
    strategy="optimize",
  ),
]

DEFAULT_METRICS_SEARCH = [
  dict(
    name="y1",
    objective="maximize",
    strategy="constraint",
    threshold=0.25,
  ),
  dict(
    name="y2",
    objective="minimize",
    strategy="constraint",
    threshold=0.75,
  ),
]

DEFAULT_CONSTRAINT_PARAMETERS = [
  dict(name="d1", type=DOUBLE_EXPERIMENT_PARAMETER_NAME, bounds=dict(min=0, max=1)),
  dict(name="d2", type=DOUBLE_EXPERIMENT_PARAMETER_NAME, bounds=dict(min=0, max=1)),
  dict(name="d3", type=DOUBLE_EXPERIMENT_PARAMETER_NAME, bounds=dict(min=0, max=1)),
  dict(name="d4", type=DOUBLE_EXPERIMENT_PARAMETER_NAME, bounds=dict(min=0, max=1)),
  dict(name="i1", type=INT_EXPERIMENT_PARAMETER_NAME, bounds=dict(min=0, max=10)),
  dict(name="i2", type=INT_EXPERIMENT_PARAMETER_NAME, bounds=dict(min=0, max=10)),
]

DEFAULT_LINEAR_CONSTRAINTS = [
  dict(
    type="greater_than",
    terms=[
      dict(name="d1", weight=1),
      dict(name="d3", weight=2),
    ],
    threshold=0.5,
  ),
  dict(
    type="less_than",
    terms=[
      dict(name="d2", weight=3),
      dict(name="d4", weight=4),
    ],
    threshold=0.9,
  ),
  dict(
    type="greater_than",
    terms=[
      dict(name="i1", weight=1),
      dict(name="i2", weight=1),
    ],
    threshold=10,
  ),
]

DEFAULT_TASKS = [dict(name="cheapest", cost=0.1), dict(name="cheap", cost=0.5), dict(name="expensive", cost=1)]

EXPERIMENT_META_WITH_CONSTRAINTS = dict(
  parameters=DEFAULT_CONSTRAINT_PARAMETERS,
  metrics=DEFAULT_METRICS,
  observation_budget=123,
  linear_constraints=DEFAULT_LINEAR_CONSTRAINTS,
)

DEFAULT_EXPERIMENT_META = dict(
  parameters=DEFAULT_PARAMETERS,
  metrics=DEFAULT_METRICS,
  observation_budget=100,
)

EXPERIMENT_META_SIMPLE = dict(
  parameters=DEFAULT_SIMPLE_PARAMETERS,
  metrics=DEFAULT_METRICS,
  observation_budget=100,
)

EXPERIMENT_META_MULTIMETRIC = dict(
  parameters=DEFAULT_SIMPLE_PARAMETERS,
  metrics=DEFAULT_METRICS_MULTIPLE,
  observation_budget=32,
)

EXPERIMENT_META_MULTITASK = dict(
  parameters=DEFAULT_SIMPLE_PARAMETERS,
  metrics=DEFAULT_METRICS,
  observation_budget=123,
  tasks=DEFAULT_TASKS,
)

EXPERIMENT_META_MULTISOLUTION = dict(
  parameters=DEFAULT_PARAMETERS,
  metrics=DEFAULT_METRICS,
  num_solutions=7,
  observation_budget=111,
)

EXPERIMENT_META_MULTIMETRIC_THRESHOLD = dict(
  parameters=DEFAULT_PARAMETERS,
  metrics=DEFAULT_METRICS_THRESHOLDS,
  observation_budget=31,
)

EXPERIMENT_META_METRIC_CONSTRAINT = dict(
  parameters=DEFAULT_SIMPLE_PARAMETERS,
  metrics=DEFAULT_METRICS_ONE_CONSTRAINT,
  observation_budget=52,
)

EXPERIMENT_META_PRIORS = dict(
  parameters=DEFAULT_PARAMETER_WITH_PRIORS,
  metrics=DEFAULT_METRICS,
  observation_budget=10,
)

EXPERIMENT_META_CONDITIONALS = dict(
  name="conditional experiment",
  metrics=[dict(name="metric")],
  observation_budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0), conditions=dict(x=["5", "10"])),
    dict(
      name="c",
      type="categorical",
      categorical_values=[dict(name="d"), dict(name="e")],
      conditions=dict(x=["10"]),
    ),
  ],
  conditionals=[
    dict(name="x", values=["1", "5", "10"]),
  ],
)

EXPERIMENT_META_MULTICONDITIONAL = dict(
  name="multiconditional experiment",
  metrics=[dict(name="metric")],
  observation_budget=37,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0), conditions=dict(y=["y1", "y2"])),
    dict(
      name="c",
      type="categorical",
      categorical_values=[dict(name="d"), dict(name="e")],
      conditions=dict(x=["x1"]),
    ),
    dict(name="d", type="int", bounds=dict(min=0, max=1), conditions=dict(z=["on"])),
  ],
  conditionals=[
    dict(name="x", values=["x1", "x2"]),
    dict(name="y", values=["y1", "y2", "y3"]),
    dict(name="z", values=["on", "off"]),
  ],
)

EXPERIMENT_META_SEARCH = dict(
  parameters=DEFAULT_PARAMETERS,
  metrics=DEFAULT_METRICS_SEARCH,
  observation_budget=97,
)

ALL_META = dict(
  conditionals=EXPERIMENT_META_CONDITIONALS,
  constraints=EXPERIMENT_META_WITH_CONSTRAINTS,
  default=DEFAULT_EXPERIMENT_META,
  multimetric=EXPERIMENT_META_MULTIMETRIC,
  multitask=EXPERIMENT_META_MULTITASK,
  multisolution=EXPERIMENT_META_MULTISOLUTION,
  multiconditional=EXPERIMENT_META_MULTICONDITIONAL,
  metric_constraint=EXPERIMENT_META_METRIC_CONSTRAINT,
  metric_threshold=EXPERIMENT_META_MULTIMETRIC_THRESHOLD,
  priors=EXPERIMENT_META_PRIORS,
  search=EXPERIMENT_META_SEARCH,
  simple=EXPERIMENT_META_SIMPLE,
)
