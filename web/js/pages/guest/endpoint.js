/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Endpoint from "../../server/endpoint/base";
import Redirect from "../../net/redirect";
import {BadParamError, NotFoundError} from "../../net/errors";
import {setLoginStateFromToken} from "../../session/set";

export default class GuestEndpoint extends Endpoint {
  parseParams(req) {
    const tokenValue = req.query.guest_token;
    if (tokenValue) {
      this.services.apiRequestor.setApiToken(tokenValue);
      return this.services.promiseApiClient
        .tokens("self")
        .fetch()
        .then(
          (token) => {
            if (token.training_run || token.experiment) {
              setLoginStateFromToken(
                req.loginState,
                token,
                req.apiTokenDetail,
                {preserveAsParentState: true},
              );
            }
            if (token.training_run) {
              return Promise.reject(new Redirect(`/run/${token.training_run}`));
            } else if (token.experiment) {
              return Promise.reject(
                new Redirect(`/experiment/${token.experiment}`),
              );
            } else {
              return Promise.reject(new BadParamError("Invalid guest token"));
            }
          },
          (err) => {
            if (err && err.isClientError && err.isClientError()) {
              return Promise.reject(
                new NotFoundError("This link has expired").chain(err),
              );
            } else {
              return Promise.reject(err);
            }
          },
        );
    } else {
      return Promise.reject(new BadParamError("Missing guest_token"));
    }
  }
}
