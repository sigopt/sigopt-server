/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../server/endpoint/loggedin";
import Redirect from "../../net/redirect";
import getRecentActivity from "./get_recent_activity";

export default class HomeEndpoint extends LoggedInReactEndpoint {
  get reactStrictMode() {
    return false;
  } // react-autocomplete not supported
  pageName() {
    return "Home";
  }

  static page = require("./page");

  parseParams(req) {
    if (!req.loginState.clientId) {
      return Promise.reject(new Redirect("/user/info"));
    }
    if (req.query.verify) {
      this.services.alertBroker.show(
        "Thanks for verifying your email!",
        "success",
      );
    }
    const pageParams = _.pick(
      req.query,
      "includeClient",
      "archived",
      "dev",
      "page",
      "query",
    );
    return Promise.all([
      this._fetchClient(req.loginState.clientId),
      this.getApiTokens(req),
      this.services.promiseApiClient
        .clients(req.loginState.clientId)
        .experiments()
        .fetch({state: "active", limit: 0, user: req.loginState.userId}),
      this.services.promiseApiClient
        .clients(req.loginState.clientId)
        .experiments()
        .fetch({state: "active", limit: 0}),
      this.services.promiseApiClient
        .clients(req.loginState.clientId)
        .projects()
        .exhaustivelyPage(),
      getRecentActivity(
        this.services.promiseApiClient,
        req.loginState.clientId,
        req.loginState.userId,
      ),
    ]).then(
      ([
        client,
        [apiToken],
        userExpCount,
        allExpCount,
        clientProjects,
        recentActivity,
      ]) => {
        const mineExperimentCount = userExpCount.count;
        const teamExperimentCount = allExpCount.count;
        let showRunsContent = false;
        const plannedUsage = req.currentUser && req.currentUser.planned_usage;
        if (plannedUsage.track && !plannedUsage.optimize) {
          showRunsContent = true;
        }
        return {
          alertBroker: req.services.alertBroker,
          apiToken: apiToken && apiToken.token,
          apiUrl: req.configBroker.get("address.api_url"),
          appUrl: req.configBroker.get("address.app_url"),
          client: client,
          clientProjects: _.indexBy(clientProjects, "id"),
          currentUser: req.currentUser,
          errorNotifier: req.services.errorNotifier,
          legacyApiClient: req.services.legacyApiClient,
          loginState: req.loginState,
          mineExperimentCount,
          navigator: req.services.navigator,
          pageParams: pageParams,
          promiseApiClient: req.services.promiseApiClient,
          recentActivity,
          showRunsContent,
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
}
