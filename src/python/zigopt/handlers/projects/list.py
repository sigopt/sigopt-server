# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.clients.base import ClientHandler
from zigopt.json.builder import PaginationJsonBuilder, ProjectJsonBuilder
from zigopt.net.errors import BadParamError
from zigopt.project.model import Project
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


SORT_FIELD_CREATED = "created"
SORT_FIELD_UPDATED = "updated"
DEFAULT_SORT_FIELD = SORT_FIELD_UPDATED


SORT_FIELDS = {
  SORT_FIELD_CREATED: (Project.id,),
  SORT_FIELD_UPDATED: (Project.date_updated, Project.id),
}


class ClientsProjectsListHandler(ClientHandler):
  """Return a list of projects for the client of the current user.
    Return a list of projects that the current user's current active client can view.
    ---
    tags:
      - "projects"
    parameters:
      - in: query
        name: deleted
        schema:
          type: boolean
        description: "If not set, query will return both deleted and not-deleted projects. If explicitly
                      true, will only return deleted projects. If explicitly false, only return non-deleted
                      projects."
      - $ref: "#/components/parameters/ClientId"
      - $ref: "#/components/parameters/pagingBefore"
      - $ref: "#/components/parameters/pagingAfter"
      - $ref: "#/components/parameters/pagingLimit"
      - $ref: "#/components/parameters/sortField"
      - $ref: "#/components/parameters/sortAscending"
    responses:
          200:
            description: "Projects returned."
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Project'
          401:
            description: "Unauthorized. Authorization was incorrect."
          400:
            description: "Bad Request Format. Failed validation of some kind."
          404:
            description: "Not found. No client is at that URI."
          429:
            description: "Client has engaged too many events recently and is rate limited."
          5XX:
            description: "Unexpected Error"
    components:
      schemas:
        PagingResponseProjects:
          allOf:
            - $ref: "#/components/schemas/PagingResponseBase"
            - type: object
              description: "Response to a paging list request for Projects."
              properties:
                data:
                  type: array
                  items:
                    $ref: '#/components/schemas/Project'
    """

  authenticator = api_token_authentication
  required_permissions = READ
  allow_development = True

  Params = ImmutableStruct(
    "Params",
    (
      "paging",
      "sort",
      "user",
      "Field",
      "deleted",
    ),
  )

  def parse_params(self, request):
    sort = request.get_sort(DEFAULT_SORT_FIELD, default_ascending=False)
    try:
      Field = SORT_FIELDS[sort.field]
    except KeyError as e:
      raise BadParamError(f"Invalid sort: {sort.field}") from e
    return self.Params(
      paging=request.get_paging(),
      sort=sort,
      user=request.optional_int_param("user"),
      Field=Field,
      deleted=request.optional_bool_param("deleted"),
    )

  def handle(self, params):
    query = self.services.database_service.query(Project, *params.Field)
    query = query.filter(Project.client_id == self.client_id)
    if params.user:
      query = query.filter(Project.created_by == params.user)
    if not params.deleted:
      query = query.filter(Project.deleted.is_(False))
    results, new_before, new_after = self.services.query_pager.fetch_page(
      q=query,
      Field=params.Field,
      paging=params.paging,
      ascending=params.sort.ascending,
    )
    count = self.services.database_service.count(query)
    projects = [r[0] for r in results]
    experiment_counts = self.services.experiment_service.count_by_projects(self.client_id, [p.id for p in projects])
    training_run_counts = self.services.training_run_service.count_by_projects(self.client_id, [p.id for p in projects])
    return PaginationJsonBuilder(
      data=[
        ProjectJsonBuilder(
          project,
          experiment_counts.get(project.id, 0),
          training_run_counts.get(project.id, 0),
        )
        for project in projects
      ],
      count=count,
      before=new_before,
      after=new_after,
    )
