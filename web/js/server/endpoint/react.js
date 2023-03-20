/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import Endpoint from "./base";
import Response from "../../net/response";
import checkPageExports from "./check_page_exports";
import {coalesce} from "../../utils";

/**
 * Base class for web endpoints that return a React element
 */
export default class ReactEndpoint extends Endpoint {
  constructor() {
    super();
    if (this.constructor.page) {
      checkPageExports(this.constructor.page);
    }
  }

  get entrypoint() {
    if (this.constructor.page) {
      return this.constructor.page.entrypoint;
    }
    return super.entrypoint;
  }

  /**
   * Whether to render the page in strict mode. In some cases, we call third party
   * components that are not compatible with strict mode, so we must disable this on a
   * case-by-case basis for certain pages
   */
  get reactStrictMode() {
    return true;
  }

  render(params) {
    const status = coalesce(params.status, 200);
    if (!_.isNumber(status)) {
      throw new Error(`Invalid status: ${status}`);
    }
    return new Response(status, this.reactElement(params));
  }

  /**
   * Returns a ReactElement to be rendered.
   */
  reactElement(params) {
    const Cls = this.constructor.page && this.constructor.page.default;
    return Cls ? <Cls {...params} /> : null;
  }
}
