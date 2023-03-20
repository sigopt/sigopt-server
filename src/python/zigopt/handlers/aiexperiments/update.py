# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.aiexperiments.base import AiExperimentHandler
from zigopt.handlers.experiments.base import BUDGET_KEY
from zigopt.handlers.experiments.update import ExperimentsUpdateHandler
from zigopt.handlers.validate.aiexperiment import validate_ai_experiment_json_dict_for_update
from zigopt.handlers.validate.validate_dict import ValidationType, get_opt_with_validation
from zigopt.net.errors import MissingJsonKeyError


class AiExperimentsUpdateHandler(AiExperimentHandler, ExperimentsUpdateHandler):
  """Update an already existing AiExperiment.
    This takes an already existing AiExperiment and sets its new values. Only the values
    that need to be changed should be included in this object, not any existing and unchanged fields. Thus,
    any field not mentioned explicitly in this PUT schema can't be changed after the AiExperiment is created.
    This is conceptually more like a RESTful PATCH call, however for historical reasons we use the PUT verb instead.

    This is complicated by arrays of objects parameters and metrics. For those arrays you do need to
    include all of the previous and new objects, because we will remove any object that is not present in the array.
    For those objects all of the same rules as creation continue to apply.
    ---
      tags:
          - "aiexperiments"
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/AiExperimentPut"
      responses:
        200:
          description: "AiExperiment updated."
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AiExperiment'
        204:
          description: "No content. If the header 'X-Response-Content: skip' is provided on the call, this will be
                        returned instead of 200, without any data."
        400:
          description: "Bad Request Format. Failed validation of some kind."
        401:
          description: "Unauthorized. Authorization was incorrect."
        404:
          description: "Not found. No AiExperiment is at that URI."
        429:
          description: "Client has engaged too many events recently and is rate limited."
        5XX:
          description: "Unexpected Error"
      components:
        schemas:
          AiExperimentPut:
            type: object
            properties:
              name:
                type: string
                description: "Human readable name for the AiExperiment."
                minLength: 1
                maxLength: 100
              no_optimize:
                type: boolean
                description: "If true, then the next suggestion will not be affected by this update. Useful for bulk
                              updates that are not affecting any parameters, metrics, etc. We will always honor this
                              field if present, we might or might not recalculate suggestions after AiExperiment updates
                              if not present."
              state:
                type: string
                enum: [deleted, active]
              parameters:
                type: array
                description: "The parameters of this AiExperiment, the independent variables that SigOpt will be
                              providing suggestions for. Any additional parameters require default values.
                              To delete a parameter, remove it from the array. If a new one is added, it must
                              have a default_value set which will be used for all currently existing runs. Type
                              of parameter CANNOT be changed. Bounds and grid will be set directly to the new values.
                              To remove a category from a categorical parameter, just don't include it in the array.
                              There must still be at least two non-deleted categories, however. Priors can be updated
                              like normal. If a transformation was set on a parameter, it cannot be changed."
                minItems: 1
                items:
                  $ref: '#/components/schemas/Parameter'
              metrics:
                type: array
                items:
                  $ref: '#/components/schemas/Metric'
                description: "Metric names cannot be changed. The number of metrics cannot be changed. Metric
                              objectives cannot be changed. Metric strategy cannot be changed. The only thing
                              that can be changed is the metric threshold- if that is set to null we will remove,
                              otherwise set to the provided value."
              parallel_bandwidth:
                type: integer
                minimum: 1
                default: 1
                description: "The number of simultaneous runs you plan to simultaneously be training and evaluating
                              during this AiExperiment. If this is included but set to NULL we will default to 1."
              budget:
                type: integer
                minimum: 1
                description: "The expected number of runs in an AiExperiment. Not doing as many runs as specified in the
                              budget will lead to SigOpt insufficiently exploring the n-dimensional parameter space.
                              Required when more than 1 optimized metric exists or for any constrained metrics.
                              Required for grid searches, multisolution or tasks enabled searches.
                              This makes our Sigopt optimizers much more effective and is recommended for all cases.
                              Cannot be updated in cases of grid searches, multi-optimized metrics, or multi-solution."
              metadata:
                type: object
                description: "Optional user provided set of key-value pairs. keys must be strings, values must be
                              strings (with limit 100 characters), ints, null, or numbers. Used for tracking on
                              client side."
    """

  @classmethod
  def validate_json_params(cls, data):
    validate_ai_experiment_json_dict_for_update(data)

  @classmethod
  def get_budget_key_and_value(cls, json_dict, runs_only):
    assert runs_only
    if BUDGET_KEY in json_dict:
      return BUDGET_KEY, get_opt_with_validation(json_dict, BUDGET_KEY, ValidationType.positive_integer)
    else:
      raise MissingJsonKeyError(BUDGET_KEY, json_dict)
