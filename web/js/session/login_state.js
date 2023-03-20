/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

const KEYS = [
  "apiToken",
  "clientId",
  "csrfToken",
  "isGuest",
  "organizationId",
  "parentState",
  "userId",
];

class LoginState {
  constructor(state) {
    this.setFrom(state);
  }

  setFrom(state) {
    _.each(_.without(KEYS, "csrfToken"), (key) => {
      this[key] = state[key];
    });
    this.csrfToken = state.csrfToken || this.csrfToken;

    if (this.parentState) {
      this.parentState = new LoginState(this.parentState);
    }
  }

  loggedOutCopy() {
    return new LoginState(_.pick(this, "csrfToken"));
  }

  toJson() {
    const ret = _.pick(_.pick(this, ...KEYS), (v) => !_.isUndefined(v));
    if (ret.parentState) {
      ret.parentState = ret.parentState.toJson();
    }
    return ret;
  }
}

export default LoginState;
