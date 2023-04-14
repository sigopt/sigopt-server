# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import time
from copy import deepcopy

from integration.enhanced_info_connection import EnhancedInfoConnection
from integration.request import IntegrationTestRequestor
from integration.v1.constants import ALL_META, AnyParameterMetaType, CoreExperimentMetaType


class WithExperiment:
  def __init__(self, conn, experiment):
    self.conn = conn
    self.experiment = experiment

  def __getattr__(self, name):
    return getattr(self.experiment, name)

  def __enter__(self):
    return self.experiment

  def __exit__(self, exc_type, exc_value, tb):
    pass


class Proxy:
  def __init__(self, underlying):
    self.underlying = underlying

  def __call__(self, *args, **kwargs):
    return self.underlying(*args, **kwargs)

  def __getattr__(self, name):
    return getattr(self.underlying, name)


class NoOptimizeWrapper(Proxy):
  def __call__(self, *args, **kwargs):
    kwargs["no_optimize"] = kwargs.get("no_optimize", True)
    return super().__call__(*args, **kwargs)


class ObservationWrapper(Proxy):
  def __getattr__(self, name):
    ret = super().__getattr__(name)
    if name in ("create", "update", "delete"):
      return NoOptimizeWrapper(ret)
    return ret


class ObservationsWrapper(Proxy):
  def __call__(self, *args, **kwargs):
    return ObservationWrapper(super().__call__(*args, **kwargs))


class ExperimentWrapper(Proxy):
  def __getattr__(self, name):
    ret = super().__getattr__(name)
    if name == "update":
      return NoOptimizeWrapper(ret)
    if name == "observations":
      return ObservationsWrapper(ret)
    return ret


class ExperimentsWrapper(Proxy):
  def __call__(self, *args, **kwargs):
    return ExperimentWrapper(self.underlying(*args, **kwargs))


class IntegrationTestConnection:
  def __init__(self, api_url, client_token=None, user_token=None, development=False):
    self.api_url = api_url
    self.user_token = user_token
    self.client_token = client_token
    self.development = development

    self.api_token = client_token
    if self.user_token and not self.development:
      self.api_token = user_token

    requestor = IntegrationTestRequestor(self.api_token)
    self.connection = EnhancedInfoConnection(
      self.api_token,
      {"User-Agent": "python-integration-test"},
      requestor=requestor,
    )
    self.connection.set_api_url(api_url)
    self.experiment_parameters: list[AnyParameterMetaType] = [
      {"name": "a", "type": "double", "bounds": {"min": 1, "max": 10}},
      {
        "name": "a1",
        "type": "double",
        "bounds": {"min": 0, "max": 2},
        "prior": {
          "name": "beta",
          "shape_a": 1.0,
          "shape_b": 2.0,
        },
      },
      {"name": "b", "type": "int", "bounds": {"min": 1, "max": 10}},
      {
        "name": "c",
        "type": "categorical",
        "categorical_values": [
          {"name": "c1"},
          {"name": "c2"},
        ],
      },
    ]

  def __getattr__(self, name):
    if name == "experiments":
      return ExperimentsWrapper(getattr(self.connection, name))
    return getattr(self.connection, name)

  def raw_request(self, method, url, params=None, json=None, headers=None):
    # pylint: disable=protected-access
    return self.driver._request(method, f"{self.api_url}{url}", params, json, headers)

  def as_client_only(self):
    return IntegrationTestConnection(self.api_url, client_token=self.client_token, user_token=None)

  def create_experiment(self, data):
    return WithExperiment(self, self._create_experiment(data, client_id=None))

  def create_any_experiment(self, **kwargs):
    client_id = kwargs.pop("client_id", None)
    params: CoreExperimentMetaType = {
      "parameters": self.experiment_parameters,
    }

    experiment_type = kwargs.get("type", None)
    experiment_meta = ALL_META.get(experiment_type, None)
    if experiment_type and experiment_meta:
      params = deepcopy(experiment_meta)

    params.update(kwargs)  # type: ignore

    return WithExperiment(self, self._create_experiment(params, client_id=client_id))

  def _create_experiment(self, data: CoreExperimentMetaType, client_id, static_value=None):
    value = str(time.time()) if static_value is None else hex(hash((static_value, "experiment")))[2:]
    data["name"] = data.get("name", f"sigopt_test_experiment_{value}")
    if client_id is None:
      session = self.sessions().fetch()
      client_id = session.client.id
      development = (session.api_token and session.api_token.development) or False
    else:
      development = False
    if client_id and not development:
      return self.clients(client_id).experiments().create(**data)
    return self.as_client_only().experiments().create(**data)

  def create_experiment_as(self, client_id):
    data = {
      "name": "sigopt_test_experiment_" + str(int(time.time())),
      "parameters": [
        {"name": "a", "type": "double", "bounds": {"min": 1, "max": 10}},
      ],
    }
    return WithExperiment(self, self.clients(client_id).experiments().create(**data))
