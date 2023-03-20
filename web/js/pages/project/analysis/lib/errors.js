/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import $ from "jquery";
import _ from "underscore";

import SigoptError from "../../../../error/base";

// Error class for when we reload saved dashboard there is some state change
// that makes it impossible to render the widget
// EX if a run is updated/deleted/moved and we lose a dimension and that key was saved
export class StaleStateError extends SigoptError {
  constructor(recoverable = false, cause, ...params) {
    super(...params);
    this.recoverable = recoverable;
    this.cause = cause;
    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, StaleStateError);
    }
  }
}

export const unsafeSeralizationChecker = (key, val) => {
  if (
    _.isBoolean(val) ||
    _.isString(val) ||
    _.isFinite(val) ||
    _.isArray(val) ||
    _.isNull(val) ||
    $.isPlainObject(val)
  ) {
    return val;
    // react-grid-layout ends up adding stuff to our layout we need to filter out
  } else if (key === "maxW" || (key === "maxH" && val === undefined)) {
    return undefined;
  } else if (_.isUndefined(val)) {
    // NOTE: this is to prevent undefined from becoming null and not collide with the string "undefined"
    throw new Error(
      `Undefined can not be properly serialized to/from JSON. Key is: ${key}, Value is ${val}`,
    );
  }

  throw new Error(
    `Unserializable parameter used in SourcePool. Key is: ${key}, Value is ${val}`,
  );
};
