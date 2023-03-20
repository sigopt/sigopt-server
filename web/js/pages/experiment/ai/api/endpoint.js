/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ExperimentEndpoint from "../../server/endpoint";

export default class AiExperimentApiEndpoint extends ExperimentEndpoint {
  pageName() {
    return "API";
  }

  static page = require("../../common/api/page");

  parseParams(req) {
    const pageParams = _.pick(req.query, "language");

    return {
      loginState: req.loginState,
      pageParams: _.all(pageParams, _.identity) && pageParams,
    };
  }
}
