/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {NotFoundError, PromptForLoginError} from "../../net/errors";

/**
 * Used for fetching resources based off of URL paths. For example,
 * when a user visits sigopt.ninja/experiments/5, we will want to make
 * an API call to fetch the experiment with ID 5. This module will
 * take care of all the necessary authentication checks, as well as
 * error handling.
 *
 * apiCall: function that takes a req and (success, error) callbacks.
 * setOnReq: Called on success, does not need to handle callbacks
 */
export default function setFromUrlMatch(apiCall, setOnReq) {
  return function (req, res, next) {
    if (req.loginState.apiToken) {
      apiCall(
        req,
        (apiObj) => {
          setOnReq(req, apiObj);
          next();
          return;
        },
        (err) => {
          const nextErr = _.contains([401], err.status)
            ? new NotFoundError()
            : err;
          next(nextErr);
          return;
        },
      );
    } else {
      next(new PromptForLoginError());
      return;
    }
  };
}
