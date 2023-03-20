/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import fs from "fs";
import path from "path";

import ConfigBroker from "../js/config/broker";
import appRoutes from "../js/server/routes/app";
import {getRoutes as staticRoutes} from "../js/server/express/static";

const configBroker = ConfigBroker.fromFile(
  process.env.sigopt_server_config_file,
);
configBroker.initialize(() => {
  fs.mkdirSync(path.join("artifacts", "web", "routes"), {recursive: true});
  fs.writeFileSync(
    path.join("artifacts", "web", "routes", "routes.json"),
    JSON.stringify({
      app: _.keys(appRoutes(configBroker)),
      static: _.pluck(staticRoutes(configBroker), 0),
    }),
  );
});
