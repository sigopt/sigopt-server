/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ProjectEndpoint from "../server/endpoint";

export default class ProjectAiExperimentsEndpoint extends ProjectEndpoint {
  pageName() {
    return "AI Experiments";
  }

  static page = require("./page");

  parseParams(req) {
    const pageParams = _.pick(req.query, "archived", "dev", "page", "query");
    return {
      pageParams,
      isAiExperiment: true,
    };
  }
}
