/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import DeadCodePlugin from "webpack-deadcode-plugin";
import nodeExternals from "webpack-node-externals";
import webpack from "webpack";

import {browserPageEntrypoint} from "./client_side_config";
import {
  developmentServerSideEntrypoint,
  productionServerSideEntrypoint,
  serverExternals,
} from "./server_side_config";

require("css-loader");
require("less-loader");
require("null-loader");

const defaultPage = require.resolve("../pages/default");

const entryPoints = [
  browserPageEntrypoint,
  defaultPage,
  developmentServerSideEntrypoint,
  productionServerSideEntrypoint,
  require.resolve("./entrypoint_template.js.ms"),
  require.resolve("./page_entrypoint"),
  require.resolve("./page_server_side"),
  require.resolve("./server_side_template.js.ms"),
];

const scripts = [require.resolve("../../scripts/generate_routes")];

const webpackConfigs = [
  require.resolve("./client_side.config.babel.js"),
  require.resolve("./server_side.config.babel.js"),
  require.resolve("./unused_code.config.babel.js"),
];

const allEntries = [...entryPoints, ...scripts, ...webpackConfigs];

export default ({
  assetRegex,
  babelLoader,
  env,
  mustacheLoader,
  rawLoader,
  sharedWebpackOptions,
}) => {
  const styleLoaders = [
    {
      test: /\.(?:css|less)$/u,
      use: ["null-loader", "css-loader"],
    },
    {
      test: /\.less$/u,
      use: "less-loader",
    },
  ];
  const assetLoader = {
    test: assetRegex,
    use: ["null-loader"],
  };
  const nodeVersion =
    env.NODE_TARGET_VERSION || process.versions.node.match(/^\d+\.\d+/u)[0];
  return _.extend({}, sharedWebpackOptions, {
    cache: undefined,
    entry: allEntries,
    devtool: false,
    output: {
      filename: "null",
      path: "/dev",
    },
    target: `node${nodeVersion}`,
    externals: [...serverExternals, nodeExternals()],
    plugins: [
      new webpack.DefinePlugin({
        "process.env.NODE_DOMAIN": JSON.stringify("server"),
      }),
      new DeadCodePlugin({
        patterns: ["web/**"],
        exclude: [
          "**/__*__/**",
          "**/node_modules/**",
          "web/js/component/glyph/support_glyph.sh",
          "web/fonts/**",
          "web/styles/less/libs/fontawesome/**",
          ...allEntries,
        ],
        failOnHint: true,
      }),
    ],
    module: {
      rules: _.flatten([
        {test: /\.m?js$/u, resolve: {fullySpecified: false}},
        babelLoader([]),
        mustacheLoader,
        rawLoader,
        styleLoaders,
        assetLoader,
        {test: /\.babelrc$/u, use: "null-loader"},
      ]),
    },
  });
};
