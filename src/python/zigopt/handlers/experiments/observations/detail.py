# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.db.util import DeleteClause
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.handlers.experiments.observations.base import ObservationHandler
from zigopt.json.builder import ObservationJsonBuilder, PaginationJsonBuilder
from zigopt.net.errors import BadParamError
from zigopt.observation.model import Observation
from zigopt.pagination.paging import Pager
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class ObservationsDetailHandler(ObservationHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self):
    assert self.experiment is not None
    assert self.observation is not None

    return ObservationJsonBuilder(self.experiment, self.observation)


class ObservationsDetailMultiHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  Args = ImmutableStruct("Args", ["paging", "sort", "deleted"])
  MAX_HISTORY_POINTS = 1000

  def parse_params(self, request):
    default_sort_key = "id"
    sort = request.get_sort(default_sort_key)
    deleted = request.optional_bool_param("deleted")
    return self.Args(
      paging=request.get_paging(),
      sort=sort,
      deleted=deleted,
    )

  def _get_sort_key(self, sort):
    # pylint: disable=too-many-return-statements
    assert self.experiment is not None
    experiment = self.experiment

    if sort.field == "timestamp":
      return lambda o: (o.timestamp, o.id)
    if sort.field == "value":
      metric_name = experiment.all_metrics[0].name
      return lambda o: (o.metric_value(experiment, metric_name), o.id)
    if sort.field.startswith("value-"):
      name = sort.field[len("value-") :]
      return lambda o: (o.metric_value(experiment, name), o.id)
    if sort.field == "value_stddev":
      metric_name = experiment.all_metrics[0].name
      return lambda o: (o.metric_value_var(experiment, metric_name), o.id)
    if sort.field.startswith("value_stddev-"):
      name = sort.field[len("value_stddev-") :]
      return lambda o: (o.metric_value_var(experiment, name), o.id)
    if sort.field.startswith("parameter-"):
      param_name = sort.field[len("parameter-") :]
      if param_name not in experiment.all_parameters_map:
        raise BadParamError(f"Unknown parameter: {param_name}")
      parameter = experiment.all_parameters_map[param_name]
      return lambda o: (o.get_assignment(parameter), o.id)
    if sort.field == "task":
      optimized_metric_name = experiment.optimized_metrics[0].name
      return lambda o: (o.task.cost, o.metric_value(experiment, optimized_metric_name), o.id)
    raise BadParamError(f"Invalid sort: {sort.field}")

  def handle(self, args):
    # pylint: disable=too-many-locals,unnecessary-lambda-assignment
    assert self.experiment is not None
    experiment = self.experiment

    paging = args.paging
    sort = args.sort
    deleted = args.deleted

    delete_clause = DeleteClause.DELETED if deleted else DeleteClause.NOT_DELETED

    total_count = self.services.observation_service.count_by_experiment(
      experiment,
      deleted=delete_clause,
    )

    if paging.limit is None and total_count > self.MAX_HISTORY_POINTS:
      raise BadParamError("This experiment has too much data to return a full history.")

    if sort.field == "id":

      def fetch_page(limit, before, after):
        return self.services.observation_service.read(
          experiment_id=experiment.id,
          limit=limit,
          before=before,
          after=after,
          ascending=sort.ascending,
          deleted=delete_clause,
        )

      observations, new_before, new_after = Pager(fetch_page).fetch(paging, Observation.id, ascending=sort.ascending)
    else:
      all_observations = self.services.observation_service.all_data(experiment)
      key = self._get_sort_key(sort)

      if deleted is not None:
        all_observations = [o for o in all_observations if o.deleted is deleted]

      observations, new_before, new_after = Pager(all_observations).fetch(paging, key, ascending=sort.ascending)

    return PaginationJsonBuilder(
      data=[ObservationJsonBuilder(experiment, observation) for observation in observations],
      count=total_count,
      before=new_before,
      after=new_after,
    )
