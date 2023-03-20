/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import setFromUrlMatch from "./match";
import {NotFoundError} from "../../net/errors";
import {isUndefinedOrNull} from "../../utils";

export default function setRunFromObservation() {
  return setFromUrlMatch(
    (req, s, e) => {
      if (isUndefinedOrNull(req.matchedExperiment.project)) {
        return e(new NotFoundError());
      }
      return req.services.promiseApiClient
        .clients(req.matchedExperiment.client)
        .projects(req.matchedExperiment.project)
        .trainingRuns()
        .fetch({
          filters: JSON.stringify([
            {
              operator: "==",
              field: "observation",
              value: req.params.observationId,
            },
          ]),
          limit: 1,
        })
        .then((data) => {
          if (data.count !== 1) {
            throw new NotFoundError();
          }
          return _.first(data.data);
        })
        .then(s, e);
    },
    (req, run) => {
      req.matchedTrainingRun = run;
    },
  );
}
