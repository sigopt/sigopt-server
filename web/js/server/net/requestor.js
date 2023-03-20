/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
// eslint-disable-next-line import/no-unresolved
import got from "got";

import Service from "../../services/base";
import {RequestError} from "../../net/errors";
import {isJsObject, isUndefinedOrNull} from "../../utils";

/**
 * Exposes a common interface for web requests to be
 * used both clientside and serverside. Using $.ajax
 * is not quite appropriate for serverside request
 * because
 *   a) jquery requires a functional DOM window
 *   b) jquery will issue OPTIONS requests before
 *      real requests, which is extraneous serverside.
 */
export default class NodeRequestor extends Service {
  request(options, success, error) {
    const {agent, data, headers, method, url} = options;
    const dataString = _.isString(data) ? data : null;
    const qs = isJsObject(data) ? data : null;
    const timeoutMillis = 10 * 1000;

    const parentError = new Error();
    got(
      url,
      _.omit(
        {
          agent: agent,
          body: dataString,
          headers: headers,
          searchParams: qs,
          method: method || "GET",
          timeout: {request: timeoutMillis},
          throwHttpErrors: false,
        },
        isUndefinedOrNull,
      ),
    )
      .then((response) => {
        const {body} = response;
        if (response.statusCode !== 200) {
          let responseJson;
          try {
            responseJson = JSON.parse(body);
          } catch (e) {
            responseJson = null;
          }
          return Promise.reject(
            new RequestError({
              message: responseJson ? responseJson.message : body,
              showNeedsLogin: _.contains([401, 403], response.statusCode),
              status: response.statusCode,
              tokenStatus: responseJson ? responseJson.token_status : null,
            }).chain(parentError),
          );
        }
        return response;
      })
      .then(({body, statusCode}) => success(body, statusCode), error);
  }
}
