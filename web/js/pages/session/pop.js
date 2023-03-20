/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Endpoint from "../../server/endpoint/base";
import Redirect from "../../net/redirect";
import popLoginState from "../../session/pop";
import {UnauthorizedError} from "../../net/errors";

export default class PopSessionEndpoint extends Endpoint {
  parseParams(req) {
    if (req.loginState.parentState) {
      const continueHref = req.body.continue;
      const wasGuest =
        req.apiTokenDetail && req.apiTokenDetail.token_type === "guest";
      popLoginState(req);
      return Promise.reject(
        new Redirect(
          continueHref || (wasGuest ? "/tokens/manage" : "/user/info"),
        ),
      );
    } else {
      return Promise.reject(new UnauthorizedError());
    }
  }
}
