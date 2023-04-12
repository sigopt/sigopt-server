# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import or_

from zigopt.common import *
from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import seconds_to_datetime
from zigopt.common.struct import ImmutableStruct
from zigopt.experiment.model import Experiment
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.validate.base import validate_period
from zigopt.handlers.validate.experiment import validate_state
from zigopt.json.builder import AiExperimentJsonBuilder, ExperimentJsonBuilder, PaginationJsonBuilder
from zigopt.membership.model import Membership, MembershipType
from zigopt.net.errors import BadParamError
from zigopt.permission.model import Permission
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ
from zigopt.user.model import User


EXPERIMENT_RECENCY = "recent"


class BaseExperimentsListHandler(Handler):
  allow_development = True

  Params = ImmutableStruct(
    "Params",
    (
      "paging",
      "state",
      "user",
      "search",
      "sort",
      "period_start",
      "period_end",
      "development",
      "include_ai",
    ),
  )

  class QueryArgs:
    def __init__(self, query, Field, use_having, ascending):
      self.query = query
      self.Field = Field
      self.use_having = use_having
      self.ascending = ascending

  @classmethod
  def make_list_item_json_builder(cls, experiment, progress_builder, project, auth):
    if experiment.runs_only:
      return AiExperimentJsonBuilder(
        experiment,
        progress_builder=progress_builder,
        project=project,
        auth=auth,
      )
    return ExperimentJsonBuilder(
      experiment,
      progress_builder=progress_builder,
      project=project,
      auth=auth,
    )

  def parse_state_param(self, request):
    state = request.optional_param("state")
    state = validate_state(coalesce(state, "active")) if not state == "all" else state
    return state

  @classmethod
  def get_include_ai_param(cls, request):
    include_ai = request.optional_bool_param("include_ai")
    if include_ai is None:
      include_ai = False
    return include_ai

  def parse_params(self, request):
    state = self.parse_state_param(request)
    search = request.optional_param("search")
    sort = request.get_sort("id", default_ascending=False)
    paging = request.get_paging()
    period_start = request.optional_int_param("period_start")
    period_end = request.optional_int_param("period_end")
    (period_start, period_end) = validate_period(period_start, period_end)
    development = request.optional_bool_param("development")
    include_ai = self.get_include_ai_param(request)

    return self.Params(
      paging=paging,
      search=search,
      state=state,
      user=request.optional_int_param("user"),
      sort=sort,
      period_start=period_start,
      period_end=period_end,
      development=development,
      include_ai=include_ai,
    )

  def get_development_filter_values(self, params):
    if self.auth.developer and self.auth.development:
      return tuple([True])
    if self.auth.developer and not self.auth.development:
      return tuple([False])
    if params.development is None:
      return (
        True,
        False,
      )
    return tuple([bool(params.development)])

  def additional_query_filters(self, query):
    return query

  def do_handle(self, params, client_ids, created_by, project=None):
    # pylint: disable=too-many-locals
    query_args = self._get_sorted_query(params)

    if params.state == "deleted":
      deleted = tuple([True])
    elif params.state == "active":
      deleted = (
        False,
        None,
      )
    else:
      deleted = (
        True,
        False,
        None,
      )

    developments = self.get_development_filter_values(params)

    if not client_ids:
      experiments_page = []
      new_before = None
      new_after = None
      count = 0
    else:
      query_args.query = (
        query_args.query.filter(Experiment.client_id.in_(client_ids))
        .filter(Experiment.deleted.in_(deleted))
        .filter(Experiment.experiment_meta.development.as_boolean().in_(developments))
      )
      if project is not None:
        query_args.query = query_args.query.filter(Experiment.project_id == project.id)

      if created_by is not None:
        query_args.query = query_args.query.filter(Experiment.created_by.in_(as_tuple(created_by)))
      if params.include_ai is False:
        query_args.query = query_args.query.filter(~Experiment.experiment_meta.runs_only.as_boolean())

      if params.search is not None:
        keyword = params.search.lower().strip()
        matching_user_ids = set(
          u_id
          for (u_id,) in flatten(
            [
              self.services.database_service.all(
                self.services.database_service.query(Permission.user_id)
                .filter(Permission.client_id.in_(client_ids))
                .join(User, Permission.user_id == User.id)
                .filter(User.name.ilike(f"%{keyword}%"))
              ),
              self.services.database_service.all(
                self.services.database_service.query(Membership.user_id)
                .join(Client, Membership.organization_id == Client.organization_id)
                .join(User, Membership.user_id == User.id)
                .filter(Client.id.in_(client_ids))
                .filter(User.name.ilike(f"%{keyword}%"))
                .filter(Membership.membership_type == MembershipType.owner)
              ),
            ]
          )
        )

        # TODO(SN-1088): Consider optimization of search ordering
        if matching_user_ids:
          search_filter = or_(Experiment.created_by.in_(matching_user_ids), Experiment.name.ilike(f"%{keyword}%"))
        else:
          search_filter = Experiment.name.ilike(f"%{keyword}%")

        query_args.query = query_args.query.filter(search_filter)

      if params.period_start:
        query_args.query = query_args.query.filter(Experiment.date_created >= seconds_to_datetime(params.period_start))

      if params.period_end:
        query_args.query = query_args.query.filter(Experiment.date_created < seconds_to_datetime(params.period_end))

      query_args.query = self.additional_query_filters(query_args.query)

      experiments_page, new_before, new_after = self._issue_query(query_args, params.paging)
      count = self.services.database_service.count(query_args.query)

    progress_map = self.services.experiment_progress_service.progress_for_experiments(experiments_page)
    experiments = self.auth.filter_can_act_on_experiments(self.services, READ, experiments_page)
    experiment_project_pairs = None
    if project is None:
      project_map = self.services.project_service.projects_for_experiments(experiments=experiments)
      experiment_project_pairs = ((e, project_map.get(e.id)) for e in experiments)
    else:
      experiment_project_pairs = ((e, project) for e in experiments)
    return PaginationJsonBuilder(
      data=[
        self.make_list_item_json_builder(
          e,
          progress_builder=progress_map[e.id].json_builder(),
          project=p,
          auth=self.auth,
        )
        for e, p in experiment_project_pairs
      ],
      count=count,
      before=new_before,
      after=new_after,
    )

  def _get_sorted_query(self, params):
    if params.sort.field == EXPERIMENT_RECENCY:
      query = self.services.database_service.query(Experiment, Experiment.date_updated)
      Field = Experiment.date_updated, Experiment.id
      use_having = False
    elif params.sort.field == "id":
      # NOTE: Include a dummy second arg so that both queries return pairs
      query = self.services.database_service.query(Experiment, Experiment.id)
      Field = Experiment.id
      use_having = False
    else:
      raise BadParamError(f"Invalid sort: {params.sort.field}")
    return self.QueryArgs(query, Field, use_having, params.sort.ascending)

  def _issue_query(self, query_args, paging):
    pairs, new_before, new_after = self.services.query_pager.fetch_page(
      query_args.query, query_args.Field, paging, use_having=query_args.use_having, ascending=query_args.ascending
    )
    experiments = [p[0] for p in pairs]
    return experiments, new_before, new_after
