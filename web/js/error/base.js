/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export default class SigoptError extends Error {
  chain(causedBy) {
    this.stack += `\nCaused by: ${causedBy.stack}`;
    return this;
  }
}
