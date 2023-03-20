/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

const healthHandler = (req, res, next) => {
  res.write("healthy");
  res.end();
};

export default function initializeHealthCheck(app) {
  const healthRouteName = "/nhealth";
  app.get(healthRouteName, healthHandler);
  app.head(healthRouteName, healthHandler);
}
