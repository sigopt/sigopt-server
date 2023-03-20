/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../../server/endpoint/loggedin";
import Redirect from "../../../net/redirect";

export default class ProjectEndpoint extends LoggedInReactEndpoint {
  get reactStrictMode() {
    return false;
  } // react-autocomplete not supported, React Select

  pageNamePrefix(req) {
    return req.matchedProject.name;
  }

  getParams(req) {
    if (!req.loginState.clientId) {
      return Promise.reject(new Redirect("/user/info"));
    }
    return Promise.all([
      this._fetchClient(req.matchedProject.client),
      this.services.promiseApiClient
        .users(req.loginState.userId)
        .permissions()
        .exhaustivelyPage(),
      this.getApiTokens(req),
      this.services.promiseApiClient
        .clients(req.matchedProject.client)
        .projects()
        .exhaustivelyPage(),
    ]).then(([client, userPermissions, [apiToken], projects]) => {
      const currentPermission = _.find(
        userPermissions,
        (r) => client && r.client.id === client.id,
      );
      const hasSharePermission = currentPermission
        ? currentPermission.can_write
        : false;
      const sharingEnabled = req.configBroker.get("features.shareLinks", true);
      const canShare = hasSharePermission && sharingEnabled;
      return super.getParams(req).then((params) =>
        _.extend({}, params, {
          alertBroker: req.services.alertBroker,
          apiToken: apiToken && apiToken.token,
          canShare,
          client: client,
          currentPermission: currentPermission,
          currentUser: req.currentUser,
          legacyApiClient: req.services.legacyApiClient,
          loginState: req.loginState,
          navigator: req.services.navigator,
          path: req.path,
          project: req.matchedProject,
          projects,
          promiseApiClient: req.services.promiseApiClient,
        }),
      );
    });
  }

  _fetchClient(clientId) {
    if (clientId) {
      return this.services.promiseApiClient.clients(clientId).fetch();
    } else {
      return Promise.resolve(null);
    }
  }
}
