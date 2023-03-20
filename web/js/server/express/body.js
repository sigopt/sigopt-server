/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import bodyParser from "body-parser";

export default function addBodyParser(app) {
  const parser = bodyParser.urlencoded({extended: false});
  app.use(/\/.*/u, (req, res, next) => {
    if (req.method === "GET") {
      req.body = {};
      return next();
    } else {
      return parser(req, res, next);
    }
  });
}
