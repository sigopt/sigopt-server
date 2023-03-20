/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

export default function setCurrentExperimentCounts() {
  return (req, res, next) => {
    if (req.currentClient) {
      const expCountPromise = req.services.promiseApiClient
        .clients(req.currentClient.id)
        .experiments()
        .fetch({include_ai: false, limit: 0});
      const aiExpCountPromise = req.services.promiseApiClient
        .clients(req.currentClient.id)
        .aiexperiments()
        .fetch({limit: 0});
      Promise.all([expCountPromise, aiExpCountPromise]).then(
        ([expCount, aiExpCount]) => {
          if (expCount) {
            req.experimentCount = expCount.count;
          } else {
            req.experimentCount = null;
          }
          if (aiExpCount) {
            req.aiExperimentCount = aiExpCount.count;
          } else {
            req.aiExperimentCount = null;
          }
          next();
        },
        (err) => {
          if (err && _.contains([404], err.status)) {
            req.experimentCount = null;
            req.aiExperimentCount = null;
            next();
            return;
          } else {
            next(err);
            return;
          }
        },
      );
    } else {
      req.experimentCount = null;
      req.aiExperimentCount = null;
      next();
      return;
    }
  };
}
