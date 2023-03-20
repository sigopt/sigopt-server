/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../../server/endpoint";

export default class AiExperimentPropertiesEndpoint extends ExperimentEndpoint {
  get reactStrictMode() {
    return false;
  } // react-bootstrap-typeahead not supported
  pageName() {
    return "Properties";
  }

  static page = require("../../common/properties/page");

  parseParams(req) {
    return Promise.all([
      this._fetchCreator(req.matchedExperiment),
      this._fetchProjects(req.matchedExperiment),
    ]).then(([creator, {currentProject, projects}]) => ({
      alertBroker: req.services.alertBroker,
      clientId: req.matchedExperiment.client,
      creator: creator,
      currentProject,
      errorNotifier: req.services.errorNotifier,
      loginState: req.loginState,
      projects,
      promiseApiClient: req.services.promiseApiClient,
    }));
  }
}
