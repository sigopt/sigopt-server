# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.experiments.base import ExperimentHandler
from zigopt.json.builder import PaginationJsonBuilder, TrainingRunJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ
from zigopt.training_run.model import TrainingRun

from libsigopt.aux.errors import SigoptValidationError


# NOTE: easier to sort by ID which is monotonically increasing, so that's an appropriate proxy for created
SORT_FIELD_CREATED = "created"
SORT_FIELD_UPDATED = "updated"
DEFAULT_SORT_FIELD = SORT_FIELD_UPDATED
SORT_FIELDS = {
  SORT_FIELD_CREATED: (TrainingRun.id,),
  SORT_FIELD_UPDATED: (TrainingRun.updated, TrainingRun.id),
}


class ExperimentsBestTrainingRunsHandler(ExperimentHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  Params = ImmutableStruct(
    "Params",
    (
      "paging",
      "sort",
      "Field",
    ),
  )

  def parse_params(self, request):
    sort = request.get_sort(DEFAULT_SORT_FIELD, default_ascending=False)
    try:
      Field = SORT_FIELDS[sort.field]
    except KeyError as e:
      raise SigoptValidationError(f"Invalid sort: {sort.field}") from e
    return self.Params(
      paging=request.get_paging(),
      sort=sort,
      Field=Field,
    )

  def handle(self, params):
    assert self.experiment is not None

    observations = self.services.observation_service.all_data(self.experiment)
    best_observations = self.services.experiment_best_observation_service.get_best_observations(
      self.experiment,
      observations,
    )
    best_observation_ids = [o.id for o in best_observations]

    query = self.services.database_service.query(TrainingRun, *params.Field)
    query = query.filter(TrainingRun.observation_id.in_(best_observation_ids))
    results, new_before, new_after = self.services.query_pager.fetch_page(
      q=query,
      Field=params.Field,
      paging=params.paging,
      ascending=params.sort.ascending,
    )
    count = self.services.database_service.count(query)
    best_training_runs = [r[0] for r in results]

    if len(best_observation_ids) > 1:
      map_observation_id_to_training_run = {btr.observation_id: btr for btr in best_training_runs}
      best_training_runs = [
        map_observation_id_to_training_run[o_id]
        for o_id in best_observation_ids
        if o_id in map_observation_id_to_training_run
      ]

    checkpoint_counts = self.services.checkpoint_service.count_by_training_run_ids([tr.id for tr in best_training_runs])
    project = self.services.project_service.find_by_client_and_id(
      client_id=self.experiment.client_id,
      project_id=self.experiment.project_id,
    )
    return PaginationJsonBuilder(
      data=[
        TrainingRunJsonBuilder(
          tr,
          checkpoint_counts.get(tr.id, 0),
          project,
        )
        for tr in best_training_runs
      ],
      count=count,
      before=new_before,
      after=new_after,
    )
