/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import AppEndpoint from "./app";
import {PromptForLoginError} from "../../net/errors";

export default class LoggedInReactEndpoint extends AppEndpoint {
  get allowGuest() {
    return false;
  }
  showSidebarNav() {
    return true;
  }
  getParams(req) {
    if (
      req.loginState.userId ||
      (this.allowGuest && req.apiTokenDetail.token_type === "guest")
    ) {
      return super.getParams(req);
    } else {
      return Promise.reject(new PromptForLoginError());
    }
  }
}
