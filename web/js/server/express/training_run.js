/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import setFromUrlMatch from "./match";

export default function setMatchedTrainingRun() {
  return setFromUrlMatch(
    (req, s, e) =>
      req.services.promiseApiClient
        .trainingRuns(req.params.trainingRunId)
        .fetch()
        .then(s, e),
    (req, trainingRun) => {
      req.matchedTrainingRun = trainingRun;
    },
  );
}
