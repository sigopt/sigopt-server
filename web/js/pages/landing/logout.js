/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Endpoint from "../../server/endpoint/base";
import Redirect from "../../net/redirect";
import validateContinueHref from "../../net/continue";

export default class LogoutEndpoint extends Endpoint {
  deleteToken = (tokenValue) => {
    return this.services.promiseApiClient
      .withApiToken(tokenValue)
      .tokens("self")
      .fetch()
      .then((token) => {
        if (token.lease_length) {
          return this.services.promiseApiClient
            .withApiToken(tokenValue)
            .tokens("self")
            .delete()
            .catch((e) =>
              _.contains([403, 404], e.status)
                ? Promise.resolve()
                : Promise.reject(e),
            );
        } else {
          return Promise.resolve(null);
        }
      });
  };

  logIam = function (req, userId) {
    req.services.logger.info(
      "sigopt.iam",
      JSON.stringify({
        requestor: {user_id: userId},
        event_name: "UserLogOut",
        request_parameters: {user_id: userId},
        response_element: {},
        response_status: "success",
      }),
    );
  };

  parseParams(req) {
    if (req.method === "POST") {
      req.forceNewCookieId = true;
      this.logIam(req, req.loginState.userId);
      const continueHref = validateContinueHref(
        req.body.continue,
        req.configBroker,
      );
      req.preferences.setFrom({
        clientId: req.loginState.clientId,
        userId: req.loginState.userId,
      });
      let logoutState = req.loginState;
      while (logoutState.parentState) {
        logoutState = logoutState.parentState;
      }
      return this.deleteToken(logoutState.apiToken).then(() => {
        req.loginState.setFrom(req.loginState.loggedOutCopy());
        return Promise.reject(new Redirect(continueHref || "/"));
      });
    }
    return Promise.reject(new Redirect("/"));
  }
}
