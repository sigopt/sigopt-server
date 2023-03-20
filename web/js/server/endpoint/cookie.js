/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Endpoint from "./base";
import JsonSerializer from "../serializer/json";
import Response from "../../net/response";
import {NotFoundError} from "../../net/errors";

export default class DecryptCookieEndpoint extends Endpoint {
  serializer() {
    return new JsonSerializer();
  }

  parseParams(req) {
    return Promise.resolve({
      cookie: req.cookieState,
      path: req.path,
    });
  }

  render(params) {
    if (process.env.ALLOW_DECRYPT_COOKIE_ENDPOINT) {
      const response = new Response(200, params.cookie);
      response.contentType = "application/json; charset=utf-8";
      return response;
    }
    // eslint-disable-next-line no-console
    console.error(
      "Refusing to return decrypted cookies without the ALLOW_DECRYPT_COOKIE_ENDPOINT environment variable",
    );
    throw new NotFoundError({path: params.path});
  }
}
