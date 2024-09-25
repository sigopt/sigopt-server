# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import operator
from collections.abc import Sequence

from sqlalchemy import cast as sql_cast
from sqlalchemy import func
from sqlalchemy import types as sql_types
from sqlalchemy.dialects.postgresql import JSONB

from zigopt.common import *
from zigopt.api.auth import api_token_authentication
from zigopt.client.model import Client
from zigopt.common.struct import ImmutableStruct
from zigopt.handlers.base.handler import Handler
from zigopt.handlers.clients.base import ClientHandler
from zigopt.handlers.organizations.base import OrganizationHandler
from zigopt.handlers.projects.base import ProjectHandler
from zigopt.handlers.training_runs.parser import TrainingRunRequestParser
from zigopt.handlers.validate.validate_dict import ValidationType, get_unvalidated, get_with_validation
from zigopt.json.builder import PaginationJsonBuilder, TrainingRunJsonBuilder
from zigopt.project.model import Project
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import TrainingRunData
from zigopt.suggestion.unprocessed.model import UnprocessedSuggestion
from zigopt.training_run.constant import NON_OPTIMIZED_SUGGESTION_TYPES
from zigopt.training_run.model import TrainingRun

from libsigopt.aux.errors import InvalidKeyError, InvalidValueError, SigoptValidationError


Filter = ImmutableStruct("Filter", ["field", "operator", "casted_value"])


class Cast:
  BOOL: "Cast"
  ID: "Cast"
  INT: "Cast"
  JSONB: "Cast"
  NUMERIC: "Cast"
  TEXT: "Cast"

  def __init__(self, sql_cast_func, validation_type, python_cast_func=identity):
    self.sql_cast_func = sql_cast_func
    self.validation_type = validation_type
    self.python_cast_func = python_cast_func


Cast.BOOL = Cast(lambda x: x.cast(sql_types.Boolean), ValidationType.boolean)
Cast.ID = Cast(lambda x: x.cast(sql_types.BigInteger), ValidationType.id)
Cast.INT = Cast(lambda x: x.cast(sql_types.BigInteger), ValidationType.integer)
Cast.JSONB = Cast(identity, ValidationType.json, lambda y: sql_cast(y, JSONB))
Cast.NUMERIC = Cast(lambda x: x.cast(sql_types.Numeric), ValidationType.number)
Cast.TEXT = Cast(lambda x: x.cast(sql_types.Text), ValidationType.string)

OPERATOR_EQ_STRING = "=="

ORDERING_OPERATORS = (operator.ge, operator.gt, operator.le, operator.lt)

STRING_TO_OPERATOR_DICT = {
  OPERATOR_EQ_STRING: operator.eq,
  "!=": operator.ne,
  ">=": operator.ge,
  ">": operator.gt,
  "<=": operator.le,
  "<": operator.lt,
  "isnull": lambda x, y: x.is_(None),
}


def sqlalchemy_operator_contains(x, y):
  return x.in_(y)


class Field:
  def __init__(self, name):
    self.name = name
    self._parts = tuple(name.split("."))

  @property
  def _key(self):
    return list_get(self._parts, 1)

  def _get_clause_and_cast(self):
    key = self._key
    sort_clauses = {
      ("id",): (TrainingRun.id, Cast.ID),
      ("client",): (TrainingRun.client_id, Cast.ID),
      ("experiment",): (TrainingRun.experiment_id, Cast.ID),
      ("observation",): (TrainingRun.observation_id, Cast.ID),
      # TODO: If we actually wanted to filter/sort by project correctly, we would need to turn
      # the provided string reference ID into an int project ID
      # However, this endpoint is scoped to the project so this is kind of pointless
      # ("project",): TrainingRun.project_id,
      ("suggestion",): (TrainingRun.suggestion_id, Cast.ID),
      ("user",): (TrainingRun.created_by, Cast.ID),
      ("created",): (func.floor(func.extract("epoch", TrainingRun.created)), Cast.INT),
      ("updated",): (func.floor(func.extract("epoch", TrainingRun.updated)), Cast.INT),
      ("finished",): (func.floor(func.extract("epoch", TrainingRun.completed)), Cast.INT),
      ("completed",): (func.floor(func.extract("epoch", TrainingRun.completed)), Cast.INT),
      ("deleted",): (TrainingRun.deleted, Cast.BOOL),
      # TODO: Get the protobuf accessors working for these nested keys
      ("assignments", key): (TrainingRun.training_run_data["a"][key], Cast.JSONB),
      ("favorite",): (TrainingRun.training_run_data["f"], Cast.BOOL),
      ("optimized_suggestion",): (
        UnprocessedSuggestion.source.notin_(NON_OPTIMIZED_SUGGESTION_TYPES),
        Cast.BOOL,
      ),
      ("logs", key, "content"): (TrainingRun.training_run_data["l"][key]["c"].astext, Cast.TEXT),
      ("metadata", key): (TrainingRun.training_run_data["m"][key], Cast.JSONB),
      ("model", "type"): (TrainingRun.training_run_data["o"]["t"].astext, Cast.TEXT),
      ("name",): (TrainingRun.training_run_data["n"].astext, Cast.TEXT),
      ("source_code", "content"): (TrainingRun.training_run_data["c"]["c"].astext, Cast.TEXT),
      ("source_code", "hash"): (TrainingRun.training_run_data["c"]["g"].astext, Cast.TEXT),
      ("state",): (TrainingRun.training_run_data["s"].astext, Cast.TEXT),
      ("values", key, "value"): (TrainingRun.training_run_data["v"][key]["v"].astext, Cast.NUMERIC),
      ("values", key, "value_stddev"): (TrainingRun.training_run_data["v"][key]["r"].astext, Cast.NUMERIC),
    }
    if self._parts not in sort_clauses:
      raise InvalidValueError(f"Invalid sort: {self.name}")
    return sort_clauses[self._parts]

  @property
  def clause(self):
    clause, cast = self._get_clause_and_cast()
    return cast.sql_cast_func(clause)

  def validate_and_interpret_value(self, value):
    _, cast = self._get_clause_and_cast()
    if not cast.validation_type.get_input_validator().is_instance(value):
      raise InvalidValueError(f"Invalid value of type {cast.validation_type.name}: {value}")
    value = cast.validation_type.get_input_validator().transform(value)
    parser = TrainingRunRequestParser()
    state_enum_descriptor = TrainingRunData.DESCRIPTOR.enum_types_by_name["TrainingRunState"]
    state_to_enum_name = map_dict(lambda x: x.name, state_enum_descriptor.values_by_number)
    key = self._key

    def get_state_values():
      # NOTE: it is a known bug that training run states are stored as enum names and enum ordinals
      enum_ordinal = parser.parse_state(value)
      enum_name = state_to_enum_name.get(enum_ordinal)
      return [str(enum_ordinal), enum_name]

    lazy_value = (
      {
        (
          "values",
          key,
          "value_stddev",
        ): lambda: value
        * value,
        ("state",): get_state_values,
      }
    ).get(self._parts, lambda: value)
    return cast, lazy_value()

  def interpret_operator(self, operator_string):
    if self.name == "state":
      if operator_string == OPERATOR_EQ_STRING:
        return sqlalchemy_operator_contains
      raise InvalidValueError(f"Only the `{OPERATOR_EQ_STRING}` operator is supported for the `state` field")
    # TODO: Allow comparing to None to find "unset" values?
    # TODO: Do we need to support .has_key?
    return STRING_TO_OPERATOR_DICT.get(operator_string)


# TODO: Combine with ExperimentTrainingRunsDetailMultiHandler
class BaseTrainingRunsDetailMultiHandler(Handler):
  Params = ImmutableStruct(
    "Params", ["filters", "paging", "base_sort_clause", "full_sort_clause", "sort_ascending", "search"]
  )

  @generator_to_list
  def _parse_filters(self, filters_param_value):
    if not filters_param_value:
      return
    try:
      filter_json = json.loads(filters_param_value)
    except ValueError as e:
      raise SigoptValidationError("Could not parse JSON for filters") from e
    if not is_sequence(filter_json):
      raise InvalidValueError("Expected JSON array for filters")
    for f in filter_json:
      field = Field(get_with_validation(f, "field", ValidationType.string))
      if field.clause is None:
        raise InvalidKeyError("clause", f"Invalid field: {field.name}")
      input_operator = get_with_validation(f, "operator", ValidationType.string)
      resolved_operator = field.interpret_operator(input_operator)
      if resolved_operator is STRING_TO_OPERATOR_DICT["isnull"]:
        cast, value = None, None
      else:
        input_value = get_unvalidated(f, "value")
        cast, value = field.validate_and_interpret_value(input_value)
      # NOTE: We need to use `is` here, since 1 == True
      can_be_ordered = not any(value is v for v in (True, False, None))
      if not can_be_ordered and resolved_operator in ORDERING_OPERATORS:
        raise InvalidValueError(f"Cannot filter the value `{input_value}` with the operator `{input_operator}`")
      if cast is None:
        casted_value = None
      else:
        casted_value = cast.python_cast_func(value)
      if resolved_operator is None:
        raise InvalidValueError(f"Invalid operator: {input_operator}")
      yield Filter(
        field=field,
        operator=resolved_operator,
        casted_value=casted_value,
      )

  def parse_params(self, request):
    search = request.optional_param("search")
    sort = request.get_sort("id")
    id_clause = Field("id").clause
    base_sort_clause = Field(sort.field).clause
    full_sort_clause = (id_clause,) if sort.field == "id" else (base_sort_clause, id_clause)
    paging = request.get_paging()
    filters = self._parse_filters(request.optional_param("filters"))
    return self.Params(
      filters=filters,
      paging=paging,
      base_sort_clause=base_sort_clause,
      full_sort_clause=full_sort_clause,
      sort_ascending=sort.ascending,
      search=search,
    )

  def _generate_response(self, params, client, project, organization):
    # pylint: disable=too-many-locals
    if client:
      query = self.services.database_service.query(TrainingRun).filter(TrainingRun.client_id == client.id)
      by_organization = False
    else:
      query = (
        self.services.database_service.query(TrainingRun)
        .join(Client, Client.id == TrainingRun.client_id)
        .filter(Client.organization_id == organization.id)
      )
      by_organization = True

    if project:
      query = query.filter(TrainingRun.project_id == project.id)

    for f in params.filters:
      if f.field.name == "optimized_suggestion":
        query = query.join(UnprocessedSuggestion, UnprocessedSuggestion.id == TrainingRun.suggestion_id)
      query = query.filter(f.operator(f.field.clause, f.casted_value))
    query = query.filter(params.base_sort_clause.isnot(None))

    if params.search is not None:
      keyword = params.search.lower().strip()
      query = query.filter(TrainingRun.training_run_data["n"].astext.cast(sql_types.Text).ilike(f"%{keyword}%"))

    training_runs, before, after = self.services.query_pager.fetch_page(
      query,
      params.full_sort_clause,
      params.paging,
      ascending=params.sort_ascending,
    )
    defined_fields = self.services.training_run_service.get_defined_fields(query, by_organization=by_organization)
    count = next(f for f in defined_fields if f.key == "id").field_count
    checkpoint_counts = self.services.checkpoint_service.count_by_training_run_ids([t.id for t in training_runs])

    projects: Sequence[Project]
    if project:
      projects = [project]
    elif client:
      projects = self.services.project_service.find_by_client_and_ids(
        client_id=client.id,
        project_ids=[t.project_id for t in training_runs],
      )
    else:
      unique_client_and_project_id = distinct([(t.client_id, t.project_id) for t in training_runs])
      projects = remove_nones_sequence(
        [
          self.services.project_service.find_by_client_and_id(
            client_id=t_cid,
            project_id=t_pid,
          )
          for (t_cid, t_pid) in unique_client_and_project_id
        ]
      )

    projects_by_id = to_map_by_key(projects, key=lambda p: p.id)

    return PaginationJsonBuilder(
      [
        TrainingRunJsonBuilder(
          training_run=training_run,
          checkpoint_count=checkpoint_counts.get(training_run.id, 0),
          project=projects_by_id[training_run.project_id],
        )
        for training_run in training_runs
      ],
      count=count,
      before=before,
      after=after,
      defined_fields=defined_fields,
    )


class ClientsTrainingRunsDetailMultiHandler(BaseTrainingRunsDetailMultiHandler, ClientHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self, params):  # type: ignore
    return self._generate_response(params, client=self.client, project=None, organization=None)


class ProjectsTrainingRunsDetailMultiHandler(BaseTrainingRunsDetailMultiHandler, ProjectHandler):
  """Return all training_runs associated with a prject.
    This will return all the training_runs with this client and project associated.
    ---
    tags:
      - "training runs"
    parameters:
      - $ref: "#/components/parameters/ClientId"
      - $ref: "#/components/parameters/ProjectReferenceId"
      - in: query
        name: filters
        schema:
          $ref: "#/components/schemas/TrainingRunFilter"
        description: "Filter out some training runs based on field filtering. Must be JSON encoded then
                      url encoded."
      - $ref: "#/components/parameters/pagingBefore"
      - $ref: "#/components/parameters/pagingAfter"
      - $ref: "#/components/parameters/pagingLimit"
      - $ref: "#/components/parameters/sortField"
      - $ref: "#/components/parameters/sortAscending"
    responses:
      200:
        description: "Training Runs returned."
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PagingResponseTrainingRuns'
      401:
        description: "Unauthorized. Authorization was incorrect."
      400:
        description: "Bad Request Format. Failed validation of some kind."
      404:
        description: "Not found. No client or project is at that URI."
      429:
        description: "Client has engaged too many events recently and is rate limited."
      5XX:
        description: "Unexpected Error"
    components:
      schemas:
        PagingResponseTrainingRuns:
          allOf:
            - $ref: "#/components/schemas/PagingResponseBase"
            - type: object
              description: "Response to a paging list request for Training Runs."
              properties:
                data:
                  type: array
                  items:
                    $ref: '#/components/schemas/TrainingRun'
        TrainingRunFilter:
          type: array
          description: "This allows a caller to pre-filter all of the training runs across many different fields.
                        A caller can include as many different fields as they like, however, only AND conjunction
                        is supported right now, no OR queries. A caller who needs OR will need to submit two queries
                        and OR-merge them on the caller side."
          items:
            description: "Object that represents a single filter."
            type: object
            required: ["field", "operator"]
            properties:
              field:
                type: string
                enum: ["id", "client", "experiment", "observation", "suggestion", "user", "created", "updated",
                       "finished", "completed", "deleted", "assignments.{KEY}", "favorite", "optimized_suggestion",
                       "logs.{KEY}.content", "metadata.{KEY}", "model", "name", "source_code.content",
                       "source_code.hash", "state", "values.{KEY}.value", "values.{KEY}.stddev"]
                description: "The name of the field of training_run we are trying to filter for. Fields of sub-objects
                              are referenced with a . operator. {KEY} is a key in the appropriate map, so that the
                              filter will be on the specified value in the map."
              operator:
                type: string
                enum: ["==", "!=", ">=", ">", "<=", "<", "isnull"]
                description: "The type of comparison to be made for this filter. For the field state, then only
                              == is allowed. If the field type is boolean (deleted, favorite, optimized_suggestion)
                              then only ==, !=, and isnull are allowed."
              value:
                oneOf:
                  - type: integer
                  - type: boolean
                  - type: string
                  - type: number
                description: "The type of this field will be what matches with with type of the field property specified
                              for this filter. So it has a wide variety of choices, but the outcome of using the wrong
                              type requires thought: attempting to filter on name with a boolean will have the server
                              cast that boolean (JSON encoded) as a string and compare that with the name field without
                              reporting an error, though it is unlikely to be what the caller intended. Attempting to
                              filter on deleted with a string, by contrast, will throw an error. This field is not
                              present in the case of the isnull operator, otherwise required."
    """

  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self, params):  # type: ignore
    return self._generate_response(
      params,
      client=self.client,
      project=self.project,
      organization=None,
    )


class OrganizationsTrainingRunsDetailMultiHandler(BaseTrainingRunsDetailMultiHandler, OrganizationHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self, params):  # type: ignore
    return self._generate_response(
      params,
      organization=self.organization,
      project=None,
      client=None,
    )
