/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import path from "path";

import getServerSideConfig from "./web/js/webpack/server_side_config";
import getSettings from "./web/js/webpack/settings";

// Example usage:
// yarn -s webpack --config=./webpack.config.script.babel.js --env=SCRIPT=<FILE_NAME>
// node ./artifacts/js_script/<FILE_NAME>

export default (env) => {
  const inputPath = path.resolve(env.SCRIPT);
  const baseConfig = getSettings({NODE_ENV: "script"}).then((settings) => {
    settings.assetLoader = () => ({
      include: settings.webDir,
      test: settings.assetRegex,
      loader: "null-loader",
    });
    return getServerSideConfig(settings);
  });

  const outputPath = path.resolve("./artifacts", "js_script");
  const filename = path.basename(inputPath);

  return baseConfig.then((config) => {
    const serverConfig = config;

    serverConfig.entry = ["source-map-support/register", inputPath];
    serverConfig.output.path = outputPath;
    serverConfig.output.filename = filename;
    serverConfig.devtool = false;
    serverConfig.cache = {
      type: "filesystem",
      cacheLocation: path.resolve(path.join(".cache", "script")),
    };

    return serverConfig;
  });
};
