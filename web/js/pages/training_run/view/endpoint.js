/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import TrainingRunEndpoint from "../server/endpoint";

export default class TrainingRunViewEndpoint extends TrainingRunEndpoint {
  pageName() {
    return "Summary";
  }

  static page = require("./page");

  parseParams(req) {
    const isGuest =
      req.apiTokenDetail && req.apiTokenDetail.token_type === "guest";
    const run = req.matchedTrainingRun;
    return Promise.all([
      this.services.promiseApiClient
        .trainingRuns(run.id)
        .checkpoints()
        .exhaustivelyPage(),
      Promise.all(
        _.map(run.files, (fileId) =>
          this.services.promiseApiClient.files(fileId).fetch(),
        ),
      ),
    ]).then(([checkpoints, files]) => ({
      checkpoints: checkpoints.reverse(),
      files,
      showHistogram: !isGuest,
    }));
  }
}
