# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication, client_token_authentication
from zigopt.handlers.aiexperiments.list_base import BaseAiExperimentsListHandler
from zigopt.handlers.clients.base import ClientHandler
from zigopt.handlers.projects.base import ProjectHandler
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


class AiExperimentsListHandler(BaseAiExperimentsListHandler):
  """Return all AiExperiments for the current users client.
    Returns a list of AiExperiments for the active client of the current user.
    ---
      tags:
          - "aiexperiments"
      parameters:
        - in: query
          name: state
          schema:
            type: string
          description: "If 'all', retrieve both deleted and active AiExperiments, otherwise just active AiExperiments."
        - $ref: "#/components/parameters/pagingBefore"
        - $ref: "#/components/parameters/pagingAfter"
        - $ref: "#/components/parameters/pagingLimit"
        - $ref: "#/components/parameters/sortField"
        - $ref: "#/components/parameters/sortAscending"
      responses:
        200:
          description: "AiExperiments returned."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PagingResponseExperiment'
        400:
          description: "Bad Request Format. Failed validation of some kind."
        401:
          description: "Unauthorized. Authorization was incorrect."
        429:
          description: "Client has engaged too many events recently and is rate limited."
        5XX:
          description: "Unexpected Error"
      components:
        schemas:
          PagingResponseAiExperiment:
            allOf:
              - $ref: "#/components/schemas/PagingResponseBase"
              - type: object
                description: "Response to a paging request for AiExperiments."
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/AiExperiment'
    """

  authenticator = client_token_authentication
  required_permissions = READ

  def handle(self, params):
    assert self.auth is not None
    return self.do_handle(params, [self.auth.current_client.id], params.user)

  def can_act_on_objects(self, requested_permission, objects):
    assert self.auth is not None
    return (
      super().can_act_on_objects(requested_permission, objects)
      and self.auth.current_client
      and self.auth.can_act_on_client(self.services, requested_permission, self.auth.current_client)
    )


class ClientsAiExperimentsListHandler(ClientHandler, BaseAiExperimentsListHandler):
  """Return all AiExperiments for the current users client.
    Returns a list of AiExperiments for the client in the URL parameter.
    ---
      tags:
          - "aiexperiments"
      parameters:
        - in: query
          name: state
          schema:
            type: string
          description: "If 'all', retrieve both deleted and active AiExperiments, otherwise just active AiExperiments."
        - $ref: "#/components/parameters/pagingBefore"
        - $ref: "#/components/parameters/pagingAfter"
        - $ref: "#/components/parameters/pagingLimit"
        - $ref: "#/components/parameters/sortField"
        - $ref: "#/components/parameters/sortAscending"
        - $ref: "#/components/parameters/ClientId"
      responses:
        200:
          description: "AiExperiments returned."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PagingResponseExperiment'
        400:
          description: "Bad Request Format. Failed validation of some kind."
        401:
          description: "Unauthorized. Authorization was incorrect."
        429:
          description: "Client has engaged too many events recently and is rate limited."
        5XX:
          description: "Unexpected Error"
      components:
        schemas:
          PagingResponseAiExperiment:
            allOf:
              - $ref: "#/components/schemas/PagingResponseBase"
              - type: object
                description: "Response to a paging request for AiExperiments."
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/AiExperiment'
    """

  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self, params):
    assert self.client is not None
    return self.do_handle(params, [self.client.id], params.user)


class ClientsProjectsAiExperimentsListHandler(ProjectHandler, BaseAiExperimentsListHandler):
  authenticator = api_token_authentication
  required_permissions = READ

  def handle(self, params):
    return self.do_handle(params, [self.client_id], params.user, project=self.project)
