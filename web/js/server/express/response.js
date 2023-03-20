/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

export const generateResponse = () => (req, res, next) =>
  req.endpoint
    .getParams(req)
    .then((endpointParams) => {
      req.endpointParams = endpointParams;
      req.endpointResponse = req.endpoint.render(endpointParams);
    })
    .then(() => next(), next);

export const sendResponse = () => (req, res, next) => {
  _.each(req.endpointResponse.headers, (value, key) => res.header(key, value));
  res.status(req.endpointResponse.status);
  req.endpoint
    .serializer()
    .serialize(req, res, req.endpointParams, req.endpointResponse);
  next();
};
