/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import DefaultResponseSerializer from "../serializer/default";
import Response from "../../net/response";
import {PAGE_TITLE} from "../../brand/constant";

/**
 * Base class for web endpoints.
 */
export default class Endpoint {
  /**
   * Configuration options for how this page is rendered.
   */
  get baseTemplateParams() {
    return {};
  }
  get entrypoint() {
    return "default";
  }

  pageName() {
    return PAGE_TITLE;
  }
  showSidebarNav() {
    return false;
  }

  /**
   * parseParams should return a Promise that resolves with the params needed
   * to render the React element. This should be a
   * JSON object. This JSON object is also forwarded
   * to the client so that the same view will be rendered.
   *
   * Alternatively, it can reject with any errors.
   */
  parseParams(/* req */) {
    return Promise.resolve({});
  }

  /**
   * getParams returns a Promise that resolves with the params needed
   * to render the React element. This should be a
   * JSON object. This JSON object is also forwarded
   * to the client so that the same view will be rendered.
   *
   * Alternatively, it can reject with any errors.
   *
   * Most endpoints should implement parseParams and not getParams.
   * The default implementation of getParams defers to parseParams,
   * but endpoints that are intended to be extended by other endpoints
   * should override getParams so that the leaf endpoints only need to
   * implement parseParams.
   */
  getParams(req) {
    return Promise.resolve(this.parseParams(req));
  }

  /**
   * render should consume the params from `parseParams` and return a Response`
   */
  render(/* params */) {
    return new Response(200, {__html: ""});
  }

  /**
   * Consumes a response
   */
  serializer() {
    return new DefaultResponseSerializer(null);
  }

  /**
   * Whether this endpoint should perform csrf validation by default.
   * If you disable this, you should either perform CSRF validation manually,
   * or ensure that this endpoint is CSRF-safe.
   */
  shouldValidateCsrf() {
    return true;
  }
}
