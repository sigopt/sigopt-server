# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.api.auth import api_token_authentication
from zigopt.handlers.experiments.create import BaseExperimentsCreateHandler
from zigopt.handlers.projects.base import ProjectHandler
from zigopt.handlers.validate.aiexperiment import validate_ai_experiment_json_dict_for_create
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.json.builder import AiExperimentJsonBuilder
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE

from libsigopt.aux.errors import MissingJsonKeyError


class ClientsProjectsAiExperimentsCreateHandler(ProjectHandler, BaseExperimentsCreateHandler):
  """Create an AiExperiment
    This creates an AiExperiment with specified parameters for the user in the specified project.
    ---
      tags:
        - "aiexperiments"
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/AiExperimentPost"
      responses:
        201:
          description: "New AiExperiment created."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AiExperiment'
        204:
          description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                        returned instead of 201."
        400:
          description: "Bad Request Format. Failed validation of some kind."
        401:
          description: "Unauthorized. Authorization was incorrect."
        404:
          description: "One of the path components (ie. client or project) was not found."
        429:
          description: "Client has engaged too many events recently and is rate limited."
        5XX:
          description: "Unexpected Error"
      components:
        tags:
          - name: aiexperiments
            description: "Operations on the AiExperiment object as a first class object"
        schemas:
          Conditionals:
            type: object
            description: "Provides the ability to turn on and off a parameter subject to various other criteria. This is
                          the setup for a conditional. Can only be specified when creating the AiExperiment."
            properties:
              name:
                type: string
                description: "Name of the conditional, so that it can be referenced by the specific parameter that wants
                              to turn it off."
              values:
                type: array
                items:
                  type: string
                minItems: 2
                description: "The potential values of the conditional. This feature is at present only available for
                                categorial parameters, which is why this must be strings."
          AiExperimentPost:
            type: object
            allOf:
              - $ref: '#/components/schemas/AiExperimentBase'

          AiExperimentBase:
            type: object
            required: [name, parameters, metrics]
            properties:
              linear_constraints:
                type: array
                items:
                  $ref: '#/components/schemas/LinearConstraint'
                description: "This gives you the ability to express linear
                              inequalities that relate multiple parameters. Only valid for offline."
              metadata:
                type: object
                description: "Optional user provided set of key-value pairs. keys must be strings, values must be
                              strings (with limit 100 characters), ints, null, or numbers. Used for tracking on
                              client side."
              metrics:
                type: array
                items:
                  $ref: '#/components/schemas/Metric'
              name:
                type: string
                description: "Human readable name for the AiExperiment."
                minLength: 1
                maxLength: 100
              num_solutions:
                type: integer
                minimum: 1
                description: "The number of (diverse) solutions that SigOpt will search for. Multiple solutions are
                              only supported when no parameters of type categorical are present."
              budget:
                type: integer
                minimum: 1
                description: "The expected number of runs in the AiExperiment.
                              Not doing as many runs as specified in the budget will lead to SigOpt insufficiently
                              exploring the n-dimensional parameter space.
                              Required when more than 1 optimized metric exists or for any constrained metrics.
                              Required for grid searches or multisolution enabled searches.
                              This makes our Sigopt optimizers much more effective and is recommended for all cases."
              conditionals:
                type: array
                description: "List of conditional on parameters associated with the AiExperiment. Can only be set at
                              beginning of experiment and not updated."
                items:
                  $ref: '#/components/schemas/Conditionals'
              parallel_bandwidth:
                type: integer
                minimum: 1
                description: "The number of simultaneous runs you plan to simultaneously be training and evaluating
                              during this AiExperiment."
              type:
                type: string
                description: "Type of experiment. Grid is a comprehensive, linear search of the n-dimensional space
                              defined by the set of parameters. Random is a random search of those parameters, without
                                optimization. Offline uses the SigOpt intelligent optimization techniques."
                enum: ["grid", "offline", "random"]
                default: "offline"
              parameters:
                type: array
                description: "The parameters of this AiExperiment, the independent variables that SigOpt will be
                              providing suggestions for."
                minItems: 1
                items:
                  $ref: '#/components/schemas/Parameter'

          AiExperiment:
            allOf:
              - $ref: '#/components/schemas/AiExperimentBase'
              - type: object
                properties:
                  client:
                    type: integer
                    description: "Id of the client that is associated with this AiExperiment."
                  created:
                    type: integer
                    description: "Epoch time for when the AiExperiment was created."
                  conditionals:
                    type: array
                    items:
                      $ref: '#/components/schemas/Conditionals'
                  id:
                    type: integer
                    description: "AiExperiment Id."
                  state:
                    type: string
                    enum: [deleted, active]
                  updated:
                    type: integer
                    description: "Epoch time of last update to the AiExperiment (including new training runs associated
                                  with the AiExperiment)."
                  user:
                    type: integer
                    description: "ID of user who created this AiExperiment."
                  progress:
                    $ref: '#/components/schemas/RunProgress'
          LinearConstraint:
            type: object
            description: "This object gives you the ability to represent mathematical relationships between multiple
                          parameters. SigOpt will only suggest runs where this holds. The equations must be in the form
                          (w1*param1) + (w2*param2) ... greater than or less than the threshold."
            properties:
              type:
                type: string
                enum: ["less_than", "greater_than"]
              threshold:
                type: number
                description: "The constant on one end of the equation."
              terms:
                type: array
                items:
                  type: object
                  properties:
                    name:
                      type: string
                      description: "Must be the name of a parameter of type double."
                    weight:
                      type: number
                      description: "The coeffcient for the specific parameter in the inequality equation."
          Metric:
            type: object
            description: "Variable that will be tracked with a run. Each one represents a dependent variable in the
                          experiment that your code must report back to prepare for the next optimization run."
            required: [name]
            properties:
              name:
                type: string
              objective:
                type: string
                enum: ["maximize", "minimize"]
                default: "maximize"
              strategy:
                type: string
                enum: ["optimize", "store", "constraint"]
                default: "optimize"
              threshold:
                type: number
                description: "What is the minimum (or maxiumum if objective is minimize) desired value for a given
                metric. What do you want this metric to be closest too? Required when metric strategy is constraint."
          Parameter:
            type: object
            required: [name, type]
            properties:
              name:
                type: string
                description: "Name of the parameter. No duplicates allowed in the array."
              type:
                type: string
                enum: ["categorical", "double", "int"]
                description: "Type of the parameter. Categorical means a set of strings, double and int are number and
                              integer, respectively."
              transformation:
                type: string
                enum: ["none", "log"]
                description: "Only an option if parameter type is double, otherwise cannot be present. If set to 'log'
                              then this will be treated as a paremeter in log-space."
              grid:
                type: array
                items:
                  oneOf:
                    - type: integer
                    - type: number
                description: "If experiment type is grid, this can be a list of values to try for this parameter. No
                              duplicates allowed."
              bounds:
                type: object
                description: "If experiment type is grid and grid is not defined for this parameter and the parameter is
                              double or int, this must be set."
                properties:
                  min:
                    oneOf:
                      - type: integer
                      - type: number
                    description: "The minimum value that the SigOpt optimizer will search. Must be same type as
                                  parameter type."
                  max:
                    oneOf:
                      - type: integer
                      - type: number
                    description: "The maxium value that the Sigopt optimizer will search. Must be same type as parameter
                                  type."
              prior:
                type: object
                description: "Only applies to parameters type of double. This allows you to define a prior belief on the
                              distribution of this parameter."
                properties:
                  name:
                    type: string
                    enum: ["normal", "beta"]
                  mean:
                    type: number
                    description: "Only applies for prior type 'normal.' This must be within any bounds provided."
                  scale:
                    type: number
                    description: "Only applies for prior type 'normal.' This number must be positive."
                  shape_a:
                    type: number
                    description: "Only applies for prior type 'beta.' This number must be positive."
                  shape_b:
                    type: number
                    description: "Only applies for prior type 'beta.' This number must be positive."
              categorical_values:
                type: array
                description: "This is the set of potential categorical values. If type is 'categorical' this is
                              required, otherwise not present. A single experiment can only have a total of 10
                              categorical values across all categorical parameters."
                items:
                    type: string
              default_value:
                description: "The default value for this parameter if not assigned. If parameter type is double and
                              transformation is log, must be positive. This is required for all parameters added after
                              experiment creation. Type must match parameter type."
                oneOf:
                  - type: integer
                  - type: number
                  - type: string
          RunProgress:
            type: object
            properties:
              finished_run_count:
                type: integer
                minimum: 0
              active_run_count:
                type: integer
                minimum: 0
              total_run_count:
                type: integer
                minimum: 0
              remaining_budget:
                nullable: true
                type: integer
    """

  # pylint: disable=useless-return

  allow_development = False
  authenticator = api_token_authentication
  required_permissions = WRITE
  budget_key = "budget"
  JsonBuilder = AiExperimentJsonBuilder
  user_facing_class_name = "AI Experiment"

  def get_client(self):
    return self.client

  def get_project(self, data, default=None):
    assert "project" not in data
    return self.project

  @classmethod
  def get_runs_only(cls, json_dict):
    assert "runs_only" not in json_dict
    return True

  @classmethod
  def get_budget_key_and_value(cls, json_dict, runs_only):
    assert "observation_budget" not in json_dict
    return cls.budget_key, get_opt_with_validation(json_dict, cls.budget_key, ValidationType.positive_integer)

  @classmethod
  def get_tasks_from_json(cls, json_dict):
    assert "tasks" not in json_dict
    return None

  @classmethod
  def get_metric_list_from_json(cls, json_dict):
    assert "metric" not in json_dict
    if not json_dict.get("metrics", []):
      raise MissingJsonKeyError("metrics", f"{cls.user_facing_class_name}s must have at least 1 metric.")
    return super().get_metric_list_from_json(json_dict)

  @classmethod
  def get_metric_name(cls, metric, seen_names, num_metrics):
    if (name := super().get_metric_name(metric, seen_names, num_metrics)) is None:
      raise MissingJsonKeyError("name", "All metrics require a name")
    return name

  @classmethod
  def validate_json_params(cls, data):
    validate_ai_experiment_json_dict_for_create(data)
