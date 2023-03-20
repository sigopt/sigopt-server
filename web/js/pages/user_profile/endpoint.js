/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../server/endpoint/loggedin";

export default class UserProfileEndpoint extends LoggedInReactEndpoint {
  pageName() {
    return "My Profile";
  }

  static page = require("./page");

  parseParams(req) {
    if (req.query.verify === "1") {
      this.services.alertBroker.show(
        "We've sent you a verification email.",
        "success",
      );
    }
    if (req.query.needs_verify === "1") {
      this.services.alertBroker.show(
        "You must verify your email before you can do that.",
        "danger",
      );
    }
    if (req.query.invalidInvite === "1") {
      this.services.alertBroker.show(
        "The Sign Up link you used is no longer valid.",
        "danger",
      );
    }
    if (req.query.newClient === "1") {
      this.services.alertBroker.show(
        `You have been added to the ${req.currentClient.name} Team at ${req.currentOrganization.name}`,
        "success",
      );
    }

    return Promise.all([
      this.services.promiseApiClient
        .users(req.loginState.userId)
        .pendingPermissions()
        .exhaustivelyPage(),
      this.services.promiseApiClient
        .users(req.loginState.userId)
        .memberships()
        .exhaustivelyPage(),
      this._fetchUserPermissionsMap(req.loginState.userId),
    ]).then(([userPendingPermissions, userMemberships, userPermissionsMap]) => {
      const emailVerificationEnabled = req.configBroker.get(
        "email.verify",
        true,
      );
      return {
        ajaxClient: this.services.ajaxClient,
        alertBroker: this.services.alertBroker,
        error: req.error,
        legacyApiClient: this.services.legacyApiClient,
        loginState: req.loginState,
        promiseApiClient: this.services.promiseApiClient,
        shouldVerifyEmail:
          emailVerificationEnabled && !req.currentUser.has_verified_email,
        user: req.currentUser,
        userMemberships,
        userPendingPermissions,
        userPermissionsMap,
      };
    });
  }

  _fetchUserPermissionsMap(userId) {
    return this.services.promiseApiClient
      .users(userId)
      .permissions()
      .exhaustivelyPage()
      .then((permissions) =>
        _.groupBy(permissions, (p) => p.client.organization),
      );
  }
}
