/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import express from "express";

import FaviconIco from "../../icons/favicon.ico";
import {isDefinedAndNotNull} from "../../utils";

const ONE_HOUR_MILLISECONDS = 60 * 60 * 1000;

const faviconServe = ["/favicon.ico", (req, res) => res.redirect(FaviconIco)];

export const getRoutes = (configBroker) => {
  const staticRoutes = configBroker.getObject("web.static_routes", {});

  return [
    faviconServe,
    ..._.map(staticRoutes, ({dir, cacheAgeHours}, path) => [
      path,
      express.static(dir, {
        maxAge: isDefinedAndNotNull(cacheAgeHours)
          ? cacheAgeHours * ONE_HOUR_MILLISECONDS
          : undefined,
      }),
    ]),
  ];
};

export default function addStaticRoutes(configBroker, app) {
  const routes = getRoutes(configBroker);

  _.each(routes, ([route, handler]) => {
    if (handler) {
      app.use(route, handler);
    }
  });
}
