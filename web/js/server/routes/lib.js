/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Endpoint from "../endpoint/base";
import Redirect from "../../net/redirect";
import Url from "../../net/url";

class RedirectEndpoint extends Endpoint {
  constructor(code, newPath, paramsGetter) {
    super();
    this.code = code;
    this.newPath = newPath;
    this.paramsGetter = paramsGetter;
  }

  parseParams(req) {
    const params = this.paramsGetter ? this.paramsGetter(req) : {};
    const path = _.isFunction(this.newPath) ? this.newPath(req) : this.newPath;
    const parsedUrl = new Url(path);
    parsedUrl.params = params;
    return Promise.reject(new Redirect(parsedUrl.toString(), this.code));
  }
}

export const redirectTo = (newPath, paramsGetter) =>
  new RedirectEndpoint(302, newPath, paramsGetter);
export const replaceWith = (newPath, paramsGetter) =>
  new RedirectEndpoint(301, newPath, paramsGetter);
