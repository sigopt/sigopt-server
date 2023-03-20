/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../../../server/endpoint/loggedin";
import Redirect from "../../../../net/redirect";

export default class UserDetailsEndpoint extends LoggedInReactEndpoint {
  pageName() {
    return "User Details";
  }

  static page = require("./page");

  parseParams(req) {
    if (!req.loginState.clientId) {
      return Promise.reject(new Redirect("/organization"));
    }
    return this._fetchUserPermissions(req).then((userPermissions) => ({
      user: req.matchedUser,
      userPermissions,
    }));
  }

  _fetchUserPermissions(req) {
    const getMatchedPermissions = (p) => p.user.id === req.matchedUser.id;
    const getCurrentOrgMembership = (m) =>
      m.organization.id === req.currentOrganization.id;
    const currentOrgMembership = _.find(
      req.currentUserMemberships,
      getCurrentOrgMembership,
    );
    const isOrganizationOwner = currentOrgMembership.type === "owner";

    if (isOrganizationOwner) {
      return this.services.promiseApiClient
        .organizations(req.currentOrganization.id)
        .permissions()
        .exhaustivelyPage()
        .then((permissions) => _.filter(permissions, getMatchedPermissions));
    } else {
      const clients = _.chain(req.currentUserPermissions)
        .filter("can_admin")
        .pluck("client")
        .value();
      return Promise.all(
        _.map(clients, (c) =>
          this.services.promiseApiClient
            .clients(c.id)
            .permissions()
            .exhaustivelyPage(),
        ),
      ).then((permissions) =>
        _.chain(permissions)
          .flatten(true)
          .filter(getMatchedPermissions)
          .value(),
      );
    }
  }
}
