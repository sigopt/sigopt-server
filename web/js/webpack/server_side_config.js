/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import nodeExternals from "webpack-node-externals";
import path from "path";
import webpack from "webpack";

import {SERVER_BUNDLE_FILE_NAME} from "./constants";

require("null-loader");
require("source-map-support");

const NULL_JS = JSON.stringify(null);

export const developmentServerSideEntrypoint = require.resolve("../server/dev");
export const productionServerSideEntrypoint = require.resolve("../server/prod");

export const serverExternals = [
  {
    // these modules are not used serverside and break if they are loaded serverside
    "plotly.js-strict-dist": NULL_JS,
    bootstrap: NULL_JS,
    scriptjs: NULL_JS,
    "utils-copy": NULL_JS,
  },
];

export default ({
  assetLoader,
  babelLoader,
  development,
  env,
  jsDir,
  mustacheLoader,
  production,
  rawLoader,
  sharedWebpackOptions,
  webArtifactsDir,
}) => {
  const serverBundleName = SERVER_BUNDLE_FILE_NAME;
  const serverSidePageLoader = {
    include: path.resolve(jsDir, "pages"),
    test: /[./]page\.js$/u,
    use: require.resolve("./page_server_side"),
  };
  const nodeVersion =
    env.NODE_TARGET_VERSION || process.versions.node.match(/^\d+\.\d+/u)[0];
  return _.extend({}, sharedWebpackOptions, {
    devServer: development
      ? {
          devMiddleware: {
            writeToDisk: true,
          },
          static: false,
        }
      : undefined,
    cache: production
      ? undefined
      : {
          type: "filesystem",
          cacheLocation: path.resolve(path.join(".cache", "server-side")),
        },
    entry: _.flatten([
      "source-map-support/register",
      development
        ? developmentServerSideEntrypoint
        : productionServerSideEntrypoint,
    ]),
    output: {
      filename: serverBundleName,
      path: path.join(webArtifactsDir, "server"),
      uniqueName: "SigOptWebServer",
    },
    devtool: "eval-cheap-module-source-map",
    target: `node${nodeVersion}`,
    externals: [
      ...serverExternals,
      nodeExternals({
        allowlist: [/\.(css|less)$/u],
      }),
    ],
    plugins: _.filter([
      development ? new webpack.HotModuleReplacementPlugin() : null,
      new webpack.DefinePlugin({
        "process.env.NODE_DOMAIN": JSON.stringify("server"),
      }),
      development
        ? (() => {
            const DevNodeServer = require("../webpack/dev_node_server").default;
            return new DevNodeServer({
              env: {sigopt_server_config_file: env.sigopt_server_config_file},
              serverBundlePath: path.join(
                webArtifactsDir,
                "server",
                serverBundleName,
              ),
            });
          })()
        : null,
      development
        ? null
        : new webpack.SourceMapDevToolPlugin({
            test: /\.js$/u,
            module: true,
            columns: true,
          }),
    ]),
    module: {
      rules: _.filter(
        [
          babelLoader([]),
          serverSidePageLoader,
          mustacheLoader,
          rawLoader,
          {
            test: /\.(css|less)$/u,
            loader: "null-loader",
          },
          assetLoader("../static"),
        ],
        (e) => Boolean(e),
      ),
    },
  });
};
