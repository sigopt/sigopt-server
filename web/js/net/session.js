/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Service from "../services/base";

export default class SessionUpdater extends Service {
  setSession = (session) =>
    this.setApiToken(
      session.api_token.token,
      session.client && session.client.id,
    );

  setApiToken = (token, clientId) =>
    this.services.ajaxClient
      .post("/push_session", {api_token: token, client_id: clientId})
      .then(() => this.services.apiRequestor.setApiToken(token));

  pushSession = (session) =>
    this.services.ajaxClient
      .post("/push_session", {
        api_token: session.api_token.token,
        store_parent_state: true,
      })
      .then(() =>
        this.services.apiRequestor.setApiToken(session.api_token.token),
      );
}
