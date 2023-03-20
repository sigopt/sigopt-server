/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {set} from "lodash";

import ObjectSource from "./object";
import {startsWith} from "../utils";

export default class EnvironmentSource {
  initialize(success) {
    const data = {};
    const prefix = "sigopt.";
    _.each(process.env, (value, key) => {
      if (startsWith(key, prefix)) {
        set(data, key.substr(prefix.length), value);
      }
    });
    this._underlying = new ObjectSource(data);
    success();
  }

  get(key) {
    return this._underlying.get(key);
  }

  allConfigsForLogging() {
    return this._underlying.allConfigsForLogging();
  }
}
