/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import fs from "fs";
import path from "path";
import {loadConfigBrokerFromDirectory} from "sigopt-config";

import appRoutes from "../js/server/routes/app";
import {getRoutes as staticRoutes} from "../js/server/express/static";

loadConfigBrokerFromDirectory(process.env.SIGOPT_SERVER_CONFIG_DIR).then(
  (configBroker) => {
    fs.mkdirSync(path.join("artifacts", "web", "routes"), {recursive: true});
    fs.writeFileSync(
      path.join("artifacts", "web", "routes", "routes.json"),
      JSON.stringify({
        app: _.keys(appRoutes(configBroker)),
        static: _.pluck(staticRoutes(configBroker), 0),
      }),
    );
  },
);
