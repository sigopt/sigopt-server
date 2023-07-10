/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Service from "../services/base";

export default class AjaxClient extends Service {
  get = (url, params) => this.request("GET", url, params);
  post = (url, params) => this.request("POST", url, params);

  request = (method, url, params) =>
    new Promise((success, error) => {
      this.services.netRequestor.request(
        {
          data: _.extend(params || {}, {csrf_token: this.options.csrfToken}),
          method: method,
          url: url,
        },
        success,
        error,
      );
    });

  serializeAs = () => this.options;
}
