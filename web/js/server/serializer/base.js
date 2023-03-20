/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export default class Serializer {
  /**
   * Writes the body of the response to `res`.
   * Responsible for ending the stream when finished.
   * Returns a promise that should be resolved when all
   * the data has been written to res.
   */
  serialize(req, res /* endpointParams, endpointResponse */) {
    res.write("");
    res.end();
    return Promise.resolve();
  }
}
