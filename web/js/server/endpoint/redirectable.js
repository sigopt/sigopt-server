/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import qs from "qs";

import ReactEndpoint from "./react";
import Url from "../../net/url";

export default class RedirectableEndpoint extends ReactEndpoint {
  getHost(urlString) {
    const url = new Url(urlString);
    // check for port when running dev/test environments
    return url.port ? `${url.host}:${url.port}` : url.host;
  }

  getUrlRedirectPath(urlString, reqPath, reqQuery) {
    const url = new Url(urlString);
    const queryString = qs.stringify(reqQuery);
    url.path = queryString ? `${reqPath}?${queryString}` : reqPath;
    return url.toString();
  }
}
