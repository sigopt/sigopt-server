/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import OrganizationAdminEndpoint from "../server/endpoint";

export default class OrganizationExperimentsEndpoint extends OrganizationAdminEndpoint {
  pageName() {
    return "Organization Experiments";
  }
  static page = require("./page");

  ownerOnly = true;

  parseParams(req) {
    // TODO(SN-1166): We are fetching the org twice here, once in the parent and here
    return this._fetchOrganization(req)
      .then((organization) =>
        Promise.all([
          this._fetchOrganizationClients(organization.id),
          this._fetchOrganizationMemberships(organization.id),
          this._fetchOrganizationPermissions(organization.id),
        ]),
      )
      .then(([clients, memberships, permissions]) => ({
        clients: clients,
        memberships: memberships,
        permissions: permissions,
      }));
  }

  _fetchOrganizationClients(organizationId) {
    if (organizationId) {
      return this.services.promiseApiClient
        .organizations(organizationId)
        .clients()
        .exhaustivelyPage();
    } else {
      return Promise.resolve([]);
    }
  }

  _fetchOrganizationMemberships(organizationId) {
    if (organizationId) {
      return this.services.promiseApiClient
        .organizations(organizationId)
        .memberships()
        .exhaustivelyPage();
    } else {
      return Promise.resolve([]);
    }
  }

  _fetchOrganizationPermissions(organizationId) {
    if (organizationId) {
      return this.services.promiseApiClient
        .organizations(organizationId)
        .permissions()
        .exhaustivelyPage();
    } else {
      return Promise.resolve([]);
    }
  }
}
