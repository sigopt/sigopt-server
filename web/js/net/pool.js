/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import $ from "jquery";
import _ from "underscore";

export default class SourcePool {
  constructor(factory) {
    this.factory = factory;
    this.sources = {};
  }

  unsafeSeralizationChecker = (unused, val) => {
    if (
      _.isBoolean(val) ||
      _.isString(val) ||
      _.isFinite(val) ||
      _.isArray(val) ||
      _.isNull(val) ||
      $.isPlainObject(val)
    ) {
      return val;
    } else if (_.isUndefined(val)) {
      // NOTE: this is to prevent undefined from becoming null and not collide with the string "undefined"
      return "undefined_FROM_unsafeSeralizationChecker_IN_pool.js";
    }

    throw new Error(
      `Unserializable parameter used in SourcePool. Paramter is: ${val}`,
    );
  };

  get(...keys) {
    const objectSafeKeys = JSON.stringify(keys, this.unsafeSeralizationChecker);
    this.sources[objectSafeKeys] =
      this.sources[objectSafeKeys] || this.factory(...keys);
    return this.sources[objectSafeKeys];
  }
}
