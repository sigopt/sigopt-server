/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export default class Redirect {
  constructor(location, code) {
    if (code < 300 || code > 399) {
      throw new Error("Invalid redirect");
    }
    this.status = code || 302;
    this.location = location;
  }
}
