/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import LoginState from "../../session/login_state";
import {validateCsrf} from "../csrf";

export default () => (req, res, next) => {
  if (req.method !== "POST") {
    return next();
  }

  if (!req.endpoint || req.endpoint.shouldValidateCsrf()) {
    return validateCsrf(
      req.loginState,
      req.body.csrf_token,
      () => next(),
      (err) => {
        req.loginState = new LoginState({});
        return next(err);
      },
    );
  } else {
    return next();
  }
};
