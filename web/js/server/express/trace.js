/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import uuidv1 from "uuid/v1";

export default function traceRequests() {
  return (req, res, next) => {
    req.id = req.headers["x-request-id"] || `node-${uuidv1()}`;
    req.traceId = req.headers["x-trace-id"] || req.id;
    next();
  };
}
