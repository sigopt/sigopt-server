/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export default class Response {
  constructor(status, body, options = null) {
    /**
     * The status code for this response. 200 for success, 4xx for client error, 5xx for server error.
     * You probably don't want to set this to 3xx for redirect manually, instead you should error with
     * an instance of Redirect.
     */
    this.status = status;

    /**
     * The response body. Can be a string or a stream, if you want to pipe this to the end user.
     * Can also be a Promise of either of these values.
     */
    this.body = body;

    /**
     * Optional response options. Currently supports {
     *    headers: Custom response headers
     * }
     */
    this._options = options || {};
  }

  get headers() {
    return this._options.headers;
  }
}
