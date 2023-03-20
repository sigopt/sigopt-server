/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";

export default class AiExperimentInformOptimizerEndpoint extends ExperimentEndpoint {
  pageName() {
    return "Inform the Optimizer";
  }

  static page = require("./page");

  parseParams() {
    return Promise.resolve({});
  }
}
