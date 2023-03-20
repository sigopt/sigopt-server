/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import setFromUrlMatch from "./match";

export default function setMatchedExperiment() {
  return setFromUrlMatch(
    (req, s, e) => {
      if (req.params.experimentId) {
        req.services.legacyApiClient.experimentDetail(
          req.params.experimentId,
          s,
          e,
        );
      } else if (req.params.aiExperimentId) {
        req.services.promiseApiClient
          .aiexperiments(req.params.aiExperimentId)
          .fetch()
          .then(s, e);
        req.isAiExperiment = true;
      }
    },

    (req, experiment) => {
      req.matchedExperiment = experiment;
    },
  );
}
