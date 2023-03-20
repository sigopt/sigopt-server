/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import popLoginState from "../../session/pop";

export default function setApiTokenDetail() {
  const setTokenDetail = (req) => {
    if (req.loginState.apiToken) {
      return req.services.promiseApiClient
        .tokens("self")
        .fetch()
        .catch((err) => {
          if (
            req.loginState.parentState &&
            _.contains([401, 403, 404], err.status)
          ) {
            popLoginState(req);
            return setTokenDetail(req);
          } else {
            return Promise.reject(err);
          }
        });
    } else {
      return Promise.resolve(null);
    }
  };

  return (req, res, next) => {
    setTokenDetail(req)
      .then((apiToken) => {
        req.apiTokenDetail = apiToken;
      })
      .catch((err) => {
        if (_.contains([401, 403, 404], err.status)) {
          req.loginState.setFrom(req.loginState.loggedOutCopy());
          return Promise.resolve(null);
        } else {
          return Promise.reject(err);
        }
      })
      .then(() => next(), next);
  };
}
