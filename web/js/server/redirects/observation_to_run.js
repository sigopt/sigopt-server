/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import LoggedInReactEndpoint from "../../server/endpoint/loggedin";
import Redirect from "../../net/redirect";

export default class ObservationToRunRedirect extends LoggedInReactEndpoint {
  parseParams(req) {
    if (!req.loginState.clientId) {
      return Promise.reject(new Redirect("/user/info"));
    }
    return Promise.reject(new Redirect(`/run/${req.matchedTrainingRun.id}`));
  }
}
