# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sigoptlite.best_assignments import BestAssignmentsLogger
from sigoptlite.broker import Broker
from sigoptlite.builders import LocalExperimentBuilder
from sigoptlite.models import FIXED_EXPERIMENT_ID, dataclass_to_dict


PRODUCT_NAME = "sigoptlite"
DEFAULT_COMPUTE_MODE = "default"
SPE_COMPUTE_MODE = "kde_only"


class LocalAPI:
  def __init__(self, compute_mode):
    self.name = "Local"
    self.broker = None
    self.best_assignments_logger = None
    self.compute_mode = compute_mode

  def experiments_post(self, experiment_json):
    experiment = LocalExperimentBuilder(experiment_json)
    self.broker = Broker(experiment, force_spe=(self.compute_mode == SPE_COMPUTE_MODE))
    self.best_assignments_logger = BestAssignmentsLogger(experiment)
    return self.experiments_get()

  def experiments_get(self, _=None):
    if self.broker is None:
      raise ValueError("Need to create an experiment first before fetching one")
    experiment_dict = dataclass_to_dict(self.broker.experiment)
    experiment_dict["progress"] = self.broker.experiment_progress_dict
    return experiment_dict

  def suggestions_post(self, _):
    if self.broker is None:
      raise ValueError("Need to create an experiment first before creating a suggestion")
    suggestion = self.broker.create_suggestion()
    return dataclass_to_dict(suggestion)

  def observations_post(self, observation_json):
    if self.broker is None:
      raise ValueError("Need to create an experiment first before creating an observation")
    if not set(observation_json.keys()) <= {"assignments", "values", "suggestion", "failed", "task"}:
      raise ValueError("Unexpected keyword argument for Observation create endpoint")
    observation = self.broker.create_observation(**observation_json)
    return observation

  def observations_get(self, _):
    if self.broker is None:
      raise ValueError("Need to create an experiment first before fetching observations")
    return self.paginate(self.broker.get_observations())

  def best_assignments_get(self, _):
    if self.broker is None:
      raise ValueError("Need to create an experiment first before fetching best assignments")
    return self.paginate(self.best_assignments_logger.fetch(self.broker.observations))

  def paginate(self, items):
    return {
      "data": list(items),
      "object": "pagination",
      "count": len(items),
      "before": None,
      "after": None,
    }


class LocalDriver:
  def __init__(self, compute_mode=DEFAULT_COMPUTE_MODE):
    if compute_mode not in [DEFAULT_COMPUTE_MODE, SPE_COMPUTE_MODE]:
      raise ValueError(f"The argument compute_mode must be either {DEFAULT_COMPUTE_MODE}  or {SPE_COMPUTE_MODE}")

    self.name = "Local"
    local_api = LocalAPI(compute_mode=compute_mode)
    self.routes = self.create_routes(local_api)

  def create_routes(self, local_api):
    return {
      "experiments": {"POST": local_api.experiments_post, "GET": local_api.experiments_get},
      "experiments/observations": {"POST": local_api.observations_post, "GET": local_api.observations_get},
      "experiments/suggestions": {"POST": local_api.suggestions_post},
      "experiments/best_assignments": {"GET": local_api.best_assignments_get},
    }

  def check_experiment_id(self, experiment_id):
    if str(experiment_id) != FIXED_EXPERIMENT_ID:
      if (isinstance(experiment_id, str) and experiment_id.isdigit()) or isinstance(experiment_id, int):
        raise Exception(
          f"The Experiment ID provided ({experiment_id}) is not associated with your local experiment.",
          f"Please use the one associated with your local experiment: {FIXED_EXPERIMENT_ID}.",
        )
      else:
        raise Exception("Please provide an Experiment ID.")

    return True

  def check_and_remove_experiment_id(self, path, method):
    if path and path[0] == "experiments":
      if len(path) >= 2 and self.check_experiment_id(path[1]):
        path.pop(1)
      elif len(path) == 1 and method == "GET":
        raise Exception(
          "Please provide an experiment id.",
        )
    return path

  def path_to_route(self, path, method):
    clean_path = self.check_and_remove_experiment_id(path, method)
    route = "/".join([path_part for path_part in clean_path if path_part and not path_part.isdigit()])
    return route

  def request(self, method, path, data, headers):
    route = self.path_to_route(path, method)
    handler = self.routes.get(route, {}).get(method)
    if handler is None:
      raise Exception(f"{PRODUCT_NAME} only supports the following routes: {' '.join(self.routes.keys())}")
    return handler(data)
