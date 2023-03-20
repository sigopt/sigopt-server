/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import onFinished from "on-finished";

import {sendToWinston} from "../../log/server_logging_service";

const TIMEOUT_EVENT = "timeout";

/**
 * Adds timeouts to every middleware function. This is intended
 * to catch errors where developers have forgotten to call their
 * async callbacks.
 */
export default function addTimeout(globalServices) {
  return (req, res, next) => {
    const [timeoutSeconds] = _.compact([
      req.endpoint && req.endpoint.timeout,
      20,
    ]);
    req.on(TIMEOUT_EVENT, () => {
      // eslint-disable-next-line no-console
      console.error("Request timed out");
      try {
        sendToWinston(globalServices, 50, "sigopt.www.timeout", {
          message: "Request timed out",
        });
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
      }
    });

    const id = setTimeout(() => req.emit(TIMEOUT_EVENT), timeoutSeconds * 1000);
    onFinished(res, () => clearTimeout(id));
    next();
  };
}
