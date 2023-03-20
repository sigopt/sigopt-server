/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import makeRoutes from "../routes";
import {DOCS_URL} from "../../net/constant";

export default function initializeRoutes(app, configBroker) {
  const routes = makeRoutes(configBroker);
  _.each(routes, (endpoint, routeName) => {
    app.get(routeName, (req, res, next) => {
      req.endpoint = endpoint;
      req.endpoint.services = req.services;
      next();
    });
    app.post(routeName, (req, res, next) => {
      req.endpoint = endpoint;
      req.endpoint.services = req.services;
      next();
    });
  });
  // send all unhandled docs requests away
  app.get("/docs/*", (req, res, next) => {
    if (!req.endpoint) {
      res.redirect(302, DOCS_URL);
    }
    next();
  });
}
