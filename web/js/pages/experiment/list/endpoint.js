/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../../server/endpoint/loggedin";
import Redirect from "../../../net/redirect";

export default class ExperimentListEndpoint extends LoggedInReactEndpoint {
  get reactStrictMode() {
    return false;
  } // react-autocomplete not supported
  pageName() {
    return "Core Experiments";
  }

  static page = require("./page");

  parseParams(req) {
    if (!req.loginState.clientId) {
      return Promise.reject(new Redirect("/user/info"));
    }
    const pageParams = _.pick(
      req.query,
      "includeClient",
      "archived",
      "dev",
      "page",
      "query",
    );
    const experimentListEndpoint = this._getListEndpoint(
      req.loginState.clientId,
    );
    return Promise.all([
      this._fetchClient(req.loginState.clientId),
      this.services.promiseApiClient
        .users(req.loginState.userId)
        .permissions()
        .exhaustivelyPage(),
      this.getApiTokens(req),
      experimentListEndpoint.fetch({
        state: "active",
        limit: 0,
        user: req.loginState.userId,
      }),
      experimentListEndpoint.fetch({state: "active", limit: 0}),
    ]).then(
      ([client, userPermissions, [apiToken], userExpCount, allExpCount]) => {
        const currentPermission = _.find(
          userPermissions,
          (r) => client && r.client.id === client.id,
        );
        const mineExperimentCount = userExpCount.count;
        const teamExperimentCount = allExpCount.count;
        return {
          alertBroker: req.services.alertBroker,
          apiToken: apiToken && apiToken.token,
          appUrl: req.configBroker.get("address.app_url"),
          client: client,
          canShare: currentPermission ? currentPermission.can_write : false,
          currentPermission: currentPermission,
          currentUser: req.currentUser,
          errorNotifier: req.services.errorNotifier,
          isAiExperiment: false,
          isSignup: Boolean(req.query.signup),
          legacyApiClient: req.services.legacyApiClient,
          loginState: req.loginState,
          mineExperimentCount,
          navigator: req.services.navigator,
          pageParams: pageParams,
          pageTitle: this.pageName(),
          promiseApiClient: req.services.promiseApiClient,
          teamExperimentCount,
        };
      },
    );
  }

  _fetchClient(clientId) {
    if (clientId) {
      return this.services.promiseApiClient.clients(clientId).fetch();
    } else {
      return Promise.resolve(null);
    }
  }

  _getListEndpoint(clientId) {
    return this.services.promiseApiClient.clients(clientId).experiments();
  }
}
