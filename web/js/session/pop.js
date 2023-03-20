/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export default function popLoginState(req) {
  const loginState = req.loginState;
  loginState.setFrom(loginState.parentState);
  req.services.apiRequestor.setApiToken(loginState.apiToken);
}
