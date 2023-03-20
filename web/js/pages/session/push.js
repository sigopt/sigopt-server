/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Endpoint from "../../server/endpoint/base";
import {NotFoundError} from "../../net/errors";
import {setLoginStateFromSession} from "../../session/set";

export default class PushSessionEndpoint extends Endpoint {
  parseParams(req) {
    const apiToken = req.body.api_token || req.loginState.apiToken;
    const clientId = req.body.client_id || req.loginState.clientId;
    const preserveAsParentState = req.body.store_parent_state || false;
    this.services.apiRequestor.setApiToken(apiToken);
    return this.services.promiseApiClient
      .sessions()
      .fetch({preferred_client_id: clientId})
      .then((session) => {
        setLoginStateFromSession(req.loginState, session, {
          preserveAsParentState,
        });
      })
      .catch((err) =>
        Promise.reject(
          _.contains([401, 403, 404], err.status) ? new NotFoundError() : err,
        ),
      );
  }
}
