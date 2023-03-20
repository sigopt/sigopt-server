/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable no-console */
import _ from "underscore";

import main from "./main";

let mainP = main();

if (module.hot) {
  module.hot.accept("./main", () => {
    mainP = mainP
      .then(({server}) => {
        server.close();
      })
      .catch((err) => {
        console.error(err);
        process.exit(1);
      })
      .then(main);
  });
  // modified from webpack/hot/signal.js https://github.com/webpack/webpack/blob/9fcaa243573005d6fdece9a3f8d89a0e8b399613/hot/signal.js
  // start
  const checkForUpdate = (fromUpdate) => {
    module.hot
      .check()
      .then((updatedModules) => {
        if (!updatedModules) {
          if (fromUpdate) {
            console.log("[HMR] Update applied.");
          } else {
            console.warn("[HMR] Cannot find update.");
          }
          return null;
        }

        return module.hot
          .apply({
            ignoreUnaccepted: true,
            onUnaccepted: function (data) {
              console.warn(
                `Ignored an update to unaccepted module ${data.chain.join(
                  " -> ",
                )}`,
              );
            },
          })
          .then(() => {
            checkForUpdate(true);
            return null;
          });
      })
      .catch((err) => {
        const status = module.hot.status();
        if (["abort", "fail"].indexOf(status) >= 0) {
          console.error("[HMR] Cannot apply update.");
          console.error(
            `[HMR] ${_.filter([err.message, err.stack]).join("\n")}`,
          );
          console.error("[HMR] Exiting until changes are made");
          process.exit(1);
        } else {
          console.error(`[HMR] Update failed: ${err.stack || err.message}`);
        }
      });
  };

  process.on("SIGUSR2", () => {
    if (module.hot.status() !== "idle") {
      console.warn(
        `[HMR] Got signal but currently in ${module.hot.status()} state.`,
      );
      console.warn("[HMR] Need to be in idle state to start hot update.");
      return;
    }
    checkForUpdate();
  });
  // end
} else {
  throw new Error(
    "HMR not enabled, you should probably be using ./web/js/server/prod.js instead",
  );
}
