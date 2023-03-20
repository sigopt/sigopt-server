/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

export default function setCurrentClient() {
  return (req, res, next) => {
    if (req.currentUser && req.loginState.clientId) {
      req.services.legacyApiClient.clientDetail(
        req.loginState.clientId,
        (currentClient) => {
          req.currentClient = currentClient;
          next();
        },
        (err) => {
          if (err && _.contains([404], err.status)) {
            req.currentClient = null;
            next();
            return;
          } else {
            next(err);
            return;
          }
        },
      );
      return;
    } else {
      req.currentClient = null;
      next();
      return;
    }
  };
}
