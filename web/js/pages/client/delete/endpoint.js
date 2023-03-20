/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../../server/endpoint/loggedin";
import Redirect from "../../../net/redirect";

export default class ClientDeleteEndpoint extends LoggedInReactEndpoint {
  static page = require("./page");
  parseParams(req) {
    const client = req.matchedClient;
    return this.services.promiseApiClient
      .users(req.currentUser.id)
      .permissions()
      .exhaustivelyPage()
      .then((permissions) => {
        const clientPermission = _.find(
          permissions,
          (p) => p.client.id === client.id,
        );
        if (req.method === "POST") {
          return this.services.promiseApiClient
            .clients(client.id)
            .delete()
            .then(() => {
              req.loginState.clientId = null;
              return Promise.reject(new Redirect("/user/info"));
            });
        } else {
          return Promise.resolve({
            client: client,
            clientPermission: clientPermission,
            loginState: req.loginState,
          });
        }
      });
  }
}
