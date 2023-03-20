/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {PYTHON_LOG_LEVELS} from "../../log/client_logging_service";
import {sendToWinston} from "../../log/server_logging_service";

export default function logRequests(globalServices) {
  return (req, res, next) => {
    sendToWinston(globalServices, PYTHON_LOG_LEVELS.info, "sigopt.www", {
      message: [`${req.method}: ${req.get("host")}${req.path}`],
    });
    next();
  };
}
