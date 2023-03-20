/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";
import Redirect from "../../../../net/redirect";

export default class ExperimentResetEndpoint extends ExperimentEndpoint {
  get entrypoint() {
    return null;
  }

  parseParams(req) {
    const experiment = req.matchedExperiment;
    const deletePromise =
      req.method === "POST"
        ? this.services.promiseApiClient
            .experiments(experiment.id)
            .observations()
            .delete()
            .then(() =>
              this.services.promiseApiClient
                .experiments(experiment.id)
                .suggestions()
                .delete(),
            )
        : Promise.resolve(null);
    return deletePromise.then(() => {
      throw new Redirect(`/experiment/${experiment.id}`);
    });
  }
}
