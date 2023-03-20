# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from copy import deepcopy


DEFAULT_EXPERIMENT_META = dict(
  name="default experiment",
  metrics=[dict(name="profit")],
  observation_budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
  ],
)

DEFAULT_AI_EXPERIMENT_META = dict(
  name="default ai experiment",
  metrics=[dict(name="profit")],
  budget=30,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
  ],
)

EXPERIMENT_META_CONDITIONALS = dict(
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

EXPERIMENT_META_MULTICONDITIONAL = dict(
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

EXPERIMENT_META_MULTIMETRIC = dict(
  name="multimetric experiment",
  metrics=[dict(name="revenue"), dict(name="sales")],
  observation_budget=50,
  parameters=[
    dict(name="a", type="int", bounds=dict(min=1, max=50)),
    dict(name="b", type="double", bounds=dict(min=-50, max=0)),
    dict(name="c", type="categorical", categorical_values=[dict(name="d"), dict(name="e")]),
  ],
)

EXPERIMENT_META_MULTIMETRIC_MINIMIZED = deepcopy(EXPERIMENT_META_MULTIMETRIC)
EXPERIMENT_META_MULTIMETRIC_MINIMIZED.update(
  metrics=[
    dict(name="m1", objective="minimize"),
    dict(name="m2", objective="minimize"),
  ],
)

EXPERIMENT_META_MULTIMETRIC_THRESHOLD = deepcopy(EXPERIMENT_META_MULTIMETRIC)
EXPERIMENT_META_MULTIMETRIC_THRESHOLD.update(
  metrics=[
    dict(name="revenue", threshold=None),
    dict(name="sales", threshold=4.0),
  ],
)

EXPERIMENT_META_MULTISOLUTION = dict(
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

EXPERIMENT_META_WITH_CONSTRAINTS = dict(
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

EXPERIMENT_META_MULTITASK = dict(
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

EXPERIMENT_META_GRID = deepcopy(DEFAULT_EXPERIMENT_META)
EXPERIMENT_META_GRID["type"] = "grid"
EXPERIMENT_META_GRID["parameters"] = [
  dict(name="a", type="int", grid=[1, 2, 3, 4, 5]),
  dict(name="b", type="double", grid=[0.1, 0.2, 0.3]),
  dict(name="c", type="categorical", categorical_values=["a", "b", "c"]),
]
del EXPERIMENT_META_GRID["observation_budget"]

EXPERIMENT_META_SEARCH = dict(
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

ALL_META = dict(
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
