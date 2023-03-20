/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ExperimentEndpoint from "../server/endpoint";

export default class ExperimentAdminEndpoint extends ExperimentEndpoint {
  pageName() {
    return "Experiment Admin Endpoint";
  }

  static page = require("./page");

  parseParams(req) {
    return Promise.all([
      this._fetchClientAndOrganization(req.matchedExperiment.client),
      this._fetchUser(req.matchedExperiment.user),
    ]).then(([{client, organization}, user]) => ({
      alertBroker: req.services.alertBroker,
      client,
      experiment: req.matchedExperiment,
      organization,
      promiseApiClient: req.services.promiseApiClient,
      user,
    }));
  }

  _fetchClientAndOrganization(clientId) {
    if (clientId) {
      return this.services.promiseApiClient
        .clients(clientId)
        .fetch()
        .then((client) =>
          this.services.promiseApiClient
            .organizations(client.organization)
            .fetch()
            .then((organization) => ({client, organization})),
        );
    } else {
      return Promise.resolve(null);
    }
  }

  _fetchUser(userId) {
    if (userId) {
      return this.services.promiseApiClient.users(userId).fetch();
    } else {
      return Promise.resolve(null);
    }
  }
}
