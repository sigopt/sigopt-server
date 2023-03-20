/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ProjectEndpoint from "../server/endpoint";
import {NotFoundError} from "../../../net/errors";

export default class ProjectRuns extends ProjectEndpoint {
  pageName() {
    return "Runs";
  }

  static page = require("./page");

  parseParams(req) {
    const clientId = req.matchedProject.client;
    const promiseApiClient = req.services.promiseApiClient;
    return this.fetchOrganizationId(clientId, promiseApiClient).then(
      (organizationId) =>
        Promise.resolve({
          organizationId,
        }),
    );
  }

  fetchOrganizationId(clientId, promiseApiClient) {
    return promiseApiClient
      .clients(clientId)
      .fetch()
      .then((client) => {
        if (client) {
          return Promise.resolve(client.organization);
        } else {
          return Promise.reject(new NotFoundError());
        }
      })
      .then((organizationId) =>
        promiseApiClient.organizations(organizationId).fetch(),
      )
      .then((organization) => {
        if (organization) {
          return Promise.resolve(organization.id);
        } else {
          return Promise.reject(new NotFoundError());
        }
      });
  }
}
