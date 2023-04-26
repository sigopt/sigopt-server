# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.experiment.model import Experiment
from zigopt.handlers.experiments.list_base import BaseExperimentsListHandler
from zigopt.json.builder import AiExperimentJsonBuilder


class BaseAiExperimentsListHandler(BaseExperimentsListHandler):
  allow_development = False

  @classmethod
  def make_list_item_json_builder(cls, experiment, progress_builder, project, auth):
    return AiExperimentJsonBuilder(
      experiment,
      progress_builder=progress_builder,
      project=project,
      auth=auth,
    )

  def parse_params(self, request):
    state = self.parse_state_param(request)
    search = request.optional_param("search")
    sort = request.get_sort("id", default_ascending=False)
    paging = request.get_paging()
    user = request.optional_int_param("user")
    return self.Params(
      paging=paging,
      search=search,
      state=state,
      user=user,
      sort=sort,
      period_start=None,
      period_end=None,
      development=None,
      include_ai=True,
    )

  @classmethod
  def get_include_ai_param(cls, request):
    return None

  # NOTE: development runs_only experiments could disappear if we don't return
  # them here.
  def get_development_filter_values(self, params):
    return (True, False)

  def additional_query_filters(self, query):
    return query.filter(~~Experiment.experiment_meta.runs_only)
