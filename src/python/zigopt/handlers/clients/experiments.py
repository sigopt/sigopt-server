# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication, client_token_authentication
from zigopt.handlers.clients.base import ClientHandler
from zigopt.handlers.experiments.list_base import BaseExperimentsListHandler
from zigopt.handlers.projects.base import ProjectHandler
from zigopt.handlers.users.base import UserHandler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class ExperimentsListHandler(BaseExperimentsListHandler):
  """Return all experiments for the current users client.
    Returns a list of experiments for the active client of the current user.
    ---
      tags:
          - "experiments"
      parameters:
        - in: query
          name: state
          schema:
            type: string
          description: "If 'all', retrieve both deleted and active experiments, otherwise just active experiments."
        - in: query
          name: period_start
          schema:
            type: integer
          description: "Epoch timestamp, only return experiments created after this point. Must be before period_end, if
                        present."
        - in: query
          name: period_end
          schema:
            type: integer
          description: "Epoch timestamp, only return experiments created before this point. Must be after period_start,
                        if present."
        - in: query
          name: development
          schema:
            type: boolean
          description: "If not set, query will return both development and not-development experiments. If explicitly
                       true, will only return development experiments. If explicitly false, only return non-development
                       experiments."
        - in: query
          name: include_ai
          schema:
            type: boolean
          description: "If present and set to false, will only return non-run-only (e.g. just CORE) experiments. For the
                        moment, we are setting the default to include AiExperiments, however you should really
                        explicitly set this because we eventually envision changing to default of false and you want
                        your code to work the same after we change the default value."
        - $ref: "#/components/parameters/pagingBefore"
        - $ref: "#/components/parameters/pagingAfter"
        - $ref: "#/components/parameters/pagingLimit"
        - $ref: "#/components/parameters/sortField"
        - $ref: "#/components/parameters/sortAscending"
      responses:
        200:
          description: "Experiments returned."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PagingResponseExperiment'
        401:
          description: "Unauthorized. Authorization was incorrect."
        400:
          description: "Bad Request Format. Failed validation of some kind."
        404:
          description: "Not found. No experiment is at that URI."
        429:
          description: "Client has engaged too many events recently and is rate limited."
        5XX:
          description: "Unexpected Error"
      components:
        parameters:
          pagingBefore:
            in: query
            name: before
            schema:
              type: string
            description: "Optional. Base64 encoded ID, that if present, want only to return items with ids before
                          this."
          pagingAfter:
            in: query
            name: after
            schema:
              type: string
            description: "Optional. Base64 encoded ID, that if present, want only to return items with ids after
                          this."
          pagingLimit:
            in: query
            name: limit
            schema:
              type: integer
              maximum: 100
              default: 100
              minimum: 0
            description: "Optional. How many items to return."
          sortField:
            in: query
            name: field
            schema:
              type: string
            description: "The name of the field to sort by. Must be a match for a field in the object requested."
          sortAscending:
            in: query
            name: ascending
            schema:
              type: boolean
              default: False
            description: "If true, the field should be sorted in ascending order. Otherwise, sorted in descending
                          order."
        schemas:
          PagingResponseExperiment:
            allOf:
              - $ref: "#/components/schemas/PagingResponseBase"
              - type: object
                description: "Response to a paging request for Experiments."
                properties:
                  data:
                    type: array
                    items:
                      anyOf:
                        - $ref: '#/components/schemas/Experiment'
                        - $ref: '#/components/schemas/AiExperiment'
          PagingResponseBase:
            type: object
            description: "Common properties of all paged responses."
            properties:
              paging:
                type: object
                description: "Specifies where in the full array this page of data represents."
                properties:
                  before:
                    type: integer
                    description: "The start point of this subarray (in data[]) in the overall list requested."
                  after:
                    type: integer
                    description: "The last point of this subarray (in data[]) in the overall list requested."
              count:
                type: integer
                description: "The number of items in the data[] array."

    """

  authenticator = client_token_authentication
  required_permissions = READ

  def handle(self, params):
    return self.do_handle(params, [self.auth.current_client.id], params.user)

  def can_act_on_objects(self, requested_permission, objects):
    return (
      super().can_act_on_objects(requested_permission, objects)
      and self.auth.current_client
      and self.auth.can_act_on_client(self.services, requested_permission, self.auth.current_client)
    )


class ClientsExperimentsHandler(ClientHandler, BaseExperimentsListHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self, params):
    return self.do_handle(params, [self.client.id], params.user)


class ClientsProjectsExperimentsHandler(ProjectHandler, BaseExperimentsListHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self, params):
    return self.do_handle(params, [self.client_id], params.user, project=self.project)


class UsersExperimentsHandler(UserHandler, BaseExperimentsListHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self, params):
    member_client_ids = [r.client_id for r in self.services.permission_service.find_by_user_id(self.user.id)]
    owned_client_ids = [c.id for c in self.services.user_service.find_owned_clients(self.user)]
    client_ids = list(set(member_client_ids + owned_client_ids))
    return self.do_handle(params, client_ids, [self.user.id])
