<!--
Copyright © 2023 Intel Corporation

SPDX-License-Identifier: Apache License 2.0
-->

# SigOpt-Lite

SigOpt-Lite is an open source tool for locally running a lightweight version of [SigOpt](https://www.sigopt.com). Sigopt-Lite contains all the computation elements of SigOpt-Server, but bypasses the need to set up servers and Docker. SigOpt-Lite gives access to the SigOpt Core Module functionality; to learn more about that, visit the [SigOpt documentation](https://docs.sigopt.com/intro/sigopt-api-modules). To learn about how to host your own SigOpt server, visit our [SigOpt-Server documentation](../#README.md) or [the official SigOpt OSS site (sigopt.org)](https://sigopt.org/).

## Installation

Executing the following command will install both the `sigopt` client (to interact with SigOpt) and the `sigoptlite` driver (to run the computations locally).

```bash
pip install 'sigopt[lite]'
```

After that is installed, a SigOpt connection object can be created in Python with the following commands.

```python
from sigopt import Connection
conn = Connection(driver="lite")
```

From this point, SigOpt Core module functionality can be accessed through `conn`, following the same patterns as detailed in the [SigOpt documentation](https://docs.sigopt.com/core-module-api-references/quick-start).

## Basic Example

Here is an example of using SigOpt-Lite.

```python
from sigopt import Connection
conn = Connection(driver="lite")
experiment_meta = dict(
  parameters=[
    dict(name="x0", type="double", bounds=dict(min=0, max=1)),
    dict(name="x1", type="int", bounds=dict(min=0, max=10)),
  ],
  metrics=[
    dict(
      name="f",
      objective="mimize",
    )
  ],
  observation_budget=20,
)
e = conn.experiments().create(**experiment_meta)
suggestion = conn.experiments(e.id).suggestions().create()
conn.experiments(e.id).observations().create(
  suggestion=suggestion.id,
  values=[{"name": "f", "value": 2}],
)
```

More SigOpt examples can be found at the [Examples GitHub Repo](https://github.com/sigopt/sigopt-examples). Note, some of those examples will not be compatible with SigOpt-Lite, including those using the AI Module.

### Compute Mode

SigOpt-Lite supports an alternative computation mode that can generate suggestions with reduced computation burden. You can activate this compute mode at `Connection` object instantiation.

```python
from sigopt import Connection
conn = Connection(driver="lite", compute_mode="kde_only")
```

## Comparing SigOpt-Lite to Calling api.sigopt.com

To support easy use of SigOpt-Lite, the calling sequences involving the `Connection` object are meant to match those for connecting with api.sigopt.com (as is directed in the [SigOpt documentation](https://docs.sigopt.com)). Still, in pursuit of simplicitly and a minimalistic installation, SigOpt-Lite does have some limitations.

### Supported API Objects and Endpoints

Sigopt-Lite functionality matches the core module of our hosted SigOpt platform, but only certain [API endpoints](https://docs.sigopt.com/core-module-api-references/api-endpoints) are available.

| Objects          | Endpoints                                                                                                                                                                                  |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Experiment       | [Create](https://docs.sigopt.com/core-module-api-references/api-endpoints/experiment-create), [Detail](https://docs.sigopt.com/core-module-api-references/api-endpoints/experiment-detail) |
| Suggestion       | [Create](https://docs.sigopt.com/core-module-api-references/api-endpoints/suggestion-create)                                                                                               |
| Observation      | [Create](https://docs.sigopt.com/core-module-api-references/api-endpoints/observation-create), [List](https://docs.sigopt.com/core-module-api-references/api-endpoints/observation-list)   |
| Best Assignments | [Detail](https://docs.sigopt.com/core-module-api-references/api-endpoints/experiment-best-assignments)                                                                                     |

## SigOpt-Lite Behavior Limitations

### Limitations

The following behavior limitations are strictly enforced in SigOpt-Lite.

- SigOpt-Lite can only run one Experiment at a time: the Experiment ID for the sole experiment is `"-1"`.
- SigOpt-Lite supports no [parallelism](https://docs.sigopt.com/advanced_experimentation/parallelism): an observation must be reported for the open suggestion before creating another unique suggestion. Parallel suggestions can be accessed through an account at [sigopt.com](https://app.sigopt.com/signup) or through the open source SigOpt-Server.
- SigOpt-Lite does not support [Grid Searh](https://docs.sigopt.com/intro/main-concepts/random_search#grid-search).

### Recommended Limitations

The following set of soft limitations are recommended by the SigOpt research team to ensure a pleasant experience using SigOpt-Lite.

- Maximum number of parameters <= 100
- Maximum number of observations <= 10,000
- Maximum categorical breadth (total number of categorical values across all [categorical parameters](https://docs.sigopt.com/intro/main-concepts/parameter_space#categorical-parameters) <= 10
- Maximum number of [parameter constraints](https://docs.sigopt.com/advanced_experimentation/parameter_constraints) <= 10
- Maximum number of unique integer constrained variables <= 10
- Maximum number of [metric constraints](https://docs.sigopt.com/advanced_experimentation/metric_constraints) <= 4
- Maximum conditionals breadth (total number of conditional values across all [conditional parameters](https://docs.sigopt.com/intro/main-concepts/parameter_space#define-conditional-parameters) <= 6
