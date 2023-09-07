/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import OrganizationAdminEndpoint from "../server/endpoint";

export default class OrganizationTeamsEndpoint extends OrganizationAdminEndpoint {
  pageName() {
    return "Organization Teams";
  }
  static page = require("./page");

  ownerOnly = false;

  parseParams(req) {
    return (
      // TODO: We are fetching the org & memberships twice, once in the parent and here
      Promise.all([
        this._fetchOrganization(req).then((organization) =>
          this._fetchUserAdminClients(organization, req.currentUser).then(
            (clients) => [organization, clients],
          ),
        ),
        this.services.promiseApiClient
          .users(req.loginState.userId)
          .memberships()
          .exhaustivelyPage(),
      ]).then(([[organization, clients], memberships]) => {
        const userMembership = _.find(
          memberships,
          (m) => m.organization.id === organization.id,
        );
        const isOwner = Boolean(
          userMembership && userMembership.type === "owner",
        );
        const canCreateTeam = isOwner;
        return {
          canCreateTeam,
          clients,
          loginState: req.loginState,
          organization,
        };
      })
    );
  }
}
