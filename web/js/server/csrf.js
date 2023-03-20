/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import crypto from "crypto";

import {BadParamError} from "../net/errors";

export const newCsrfToken = () => crypto.randomBytes(20).toString("hex");

export const validateCsrf = (loginState, csrfToken, success, error) => {
  if (!csrfToken) {
    error(new BadParamError("Missing csrf token"));
    return;
  }
  if (loginState.csrfToken !== csrfToken) {
    error(new BadParamError("Invalid csrf token"));
    return;
  }
  success();
  return;
};
