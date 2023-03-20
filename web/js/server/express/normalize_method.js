/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export default (req, res, next) => {
  req.method = req.method?.toUpperCase();
  next();
};
