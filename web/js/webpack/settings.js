/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import fs from "fs";
import path from "path";

require("babel-loader");
require("file-loader");
require("raw-loader");

const mustacheLoaderPath = require.resolve("./mustache_loader");

const babelConfig = JSON.parse(
  fs.readFileSync(require.resolve("../../../.babelrc")),
);

export default (env = {}) =>
  new Promise((success) => {
    const jsDir = path.resolve("web/js");
    const webArtifactsDir = path.resolve("artifacts/web");
    const webDir = path.resolve("web");
    const PROD = "production";
    const DEV = "development";
    // TODO(SN-1028): we never set NODE_ENV=staging; but we should (and security)
    const nodeEnv = env.NODE_ENV || PROD;
    const production = nodeEnv === PROD;
    const development = nodeEnv === DEV;
    const hashDigest = "hex";
    const hashDigestLength = 40;
    const hashFunction = "sha1";
    const defaultPublicPath = "/static/a";
    let publicPath = env.PUBLIC_PATH || defaultPublicPath;
    if (!publicPath.endsWith("/")) {
      publicPath += "/";
    }
    const assetRegex = /\.(eot|gif|jpe?g|ico|pdf|png|svg|ttf|woff2?)$/u;
    const assetLoader = (outputPath) => ({
      test: assetRegex,
      use: [
        {
          loader: "file-loader",
          options: {
            context: webDir,
            emitFile: true,
            name: production
              ? `[${hashFunction}:hash:${hashDigest}:${hashDigestLength}]/[path][name].[ext]`
              : "[path][name].[ext]",
            outputPath,
            publicPath,
          },
        },
      ],
    });
    const mustacheLoader = {
      include: webDir,
      test: /\.ms$/u,
      use: mustacheLoaderPath,
    };
    const babelLoader = (plugins) => ({
      test: /\.js$/u,
      include: webDir,
      loader: "babel-loader",
      options: _.extend({}, babelConfig, {
        compact: production,
        plugins: [...babelConfig.plugins, ...plugins],
      }),
    });
    const rawLoader = {
      include: webDir,
      test: /\.(sql|txt)$/u,
      use: "raw-loader",
    };
    success({
      assetLoader,
      assetRegex,
      babelLoader,
      development,
      env,
      hashDigest,
      hashDigestLength,
      hashFunction,
      jsDir,
      mustacheLoader,
      production,
      publicPath,
      rawLoader,
      sharedWebpackOptions: {
        mode: development ? DEV : PROD,
      },
      webArtifactsDir,
      webDir,
    });
    return;
  });
