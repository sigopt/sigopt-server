/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

const KEYS = ["userId", "clientId"];

export default class Preferences {
  constructor(prefs) {
    this.preferences = {};
    this.setFrom(prefs || {});
  }

  setFrom(prefs) {
    _.each(KEYS, (key) => {
      this.preferences[key] = prefs[key];
    });
  }

  get clientId() {
    return this.preferences.clientId;
  }

  get userId() {
    return this.preferences.userId;
  }

  get json() {
    return _.pick(this.preferences, ...KEYS);
  }
}
