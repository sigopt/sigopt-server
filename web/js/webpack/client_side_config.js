/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import MiniCssExtractPlugin from "mini-css-extract-plugin";
import TerserPlugin from "terser-webpack-plugin";
import WebpackGlobEntriesPlugin from "webpack-glob-entries-plugin";
import path from "path";
import webpack from "webpack";
import {WebpackManifestPlugin as ManifestPlugin} from "webpack-manifest-plugin";

import {ENTRY_MANIFEST_FILE_NAME} from "./constants";

// NOTE: The trailing slash was recommended by webpack.
// It seems to resolve to node_modules/buffer instead of the built-in buffer module
// which is exactly what we want.
require("buffer/");
require("css-loader");
require("less-loader");
require("null-loader");
require("process/browser");
require("stream-browserify");

const NULL_JS = JSON.stringify(null);

const webpackPageEntrypointLoader = require.resolve("./page_entrypoint");
export const browserPageEntrypoint = require.resolve("../pages/entry.js");

export default ({
  assetLoader,
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
  sharedWebpackOptions,
  webArtifactsDir,
}) => {
  const manifestName = ENTRY_MANIFEST_FILE_NAME;
  const emittedAssetName = (baseAssetName) =>
    production ? `[contenthash]/${baseAssetName}` : baseAssetName;
  const sslOptions = development
    ? _.mapObject(
        {
          ca: "root-ca.crt",
          cert: "tls.crt",
          key: "tls.key",
        },
        (name) => path.resolve("artifacts", "tls", name),
      )
    : {};
  const clientSideStyleLoaders = [
    {
      test: /\.(css|less)$/u,
      use: ["null-loader", MiniCssExtractPlugin.loader, "css-loader"],
    },
    {
      test: /\.less$/u,
      use: "less-loader",
    },
  ];
  const clientSidePageLoader = {
    include: path.resolve(jsDir, "pages"),
    test: /[./]page\.js$/u,
    use: webpackPageEntrypointLoader,
  };
  const clientSideDevtool = development
    ? "eval-cheap-module-source-map"
    : false;
  const sourceMapFilename = "[file].map";
  const clientSideSourceMapPlugin = development
    ? null
    : new webpack.SourceMapDevToolPlugin({
        filename: sourceMapFilename,
        test: /\.js$/u,
        module: true,
        columns: true,
        noSources: true,
        publicPath,
      });
  const entryWatcher = new WebpackGlobEntriesPlugin(
    path.join(jsDir, "pages/{default,**/{*.,}page}.js"),
    {
      mapEntryName(entry) {
        const entryPath = path.parse(
          path.relative(path.join(jsDir, "pages"), entry),
        );
        return path.join(entryPath.dir, entryPath.name);
      },
    },
  );
  const entries = entryWatcher.entries();
  return _.extend({}, sharedWebpackOptions, {
    devServer: development
      ? {
          client: {
            webSocketURL: "wss://sigopt.ninja:4443/webpack/ws",
          },
          allowedHosts: "all",
          static: {
            directory: path.join(webArtifactsDir, "static"),
            watch: false,
          },
          devMiddleware: {
            index: true,
            writeToDisk: true,
          },
          compress: true,
          host: env.ASSETS_HOST || "0.0.0.0",
          port: parseInt(env.ASSETS_PORT, 10) || 7800,
          server: {
            type: "https",
            options: sslOptions,
          },
          headers: {
            "Access-Control-Allow-Origin": "*",
          },
        }
      : undefined,
    cache: production
      ? undefined
      : {
          type: "filesystem",
          cacheLocation: path.resolve(path.join(".cache", "client-side")),
        },
    entry: () =>
      entries().then((singleEntries) =>
        _.mapObject(singleEntries, (entry) => [browserPageEntrypoint, entry]),
      ),
    devtool: clientSideDevtool,
    output: {
      chunkFilename: emittedAssetName(`chunk/[name].js`),
      filename: emittedAssetName("js/pages/[name].js"),
      hashDigest,
      hashDigestLength,
      hashFunction,
      libraryTarget: "umd",
      path: path.join(webArtifactsDir, "static"),
      publicPath,
      uniqueName: "SigOptWebClient",
    },
    target: "web",
    stats: {
      children: false,
    },
    externals: {
      btoa: "btoa",
      "utils-copy": NULL_JS,
      yaml: NULL_JS,
    },
    resolve: _.extend({}, sharedWebpackOptions.resolve, {
      alias: {
        lodash: "lodash-es",
        underscore: "underscore/underscore-esm",
      },
      fallback: {
        buffer: require.resolve("buffer/"),
        stream: require.resolve("stream-browserify"),
      },
    }),
    optimization: {
      minimize: production,
      minimizer: [
        new TerserPlugin({
          parallel: 8,
          terserOptions: {
            compress: {
              booleans: true,
              collapse_vars: true,
              comparisons: true,
              conditionals: true,
              dead_code: true,
              drop_console: true,
              drop_debugger: true,
              evaluate: true,
              hoist_funs: true,
              if_return: true,
              join_vars: true,
              loops: true,
              negate_iife: true,
              properties: true,
              pure_getters: true,
              reduce_vars: true,
              sequences: true,
              unused: true,
              unsafe: false,
              unsafe_comps: false,
            },
          },
        }),
      ],
      runtimeChunk: development ? "single" : undefined,
      splitChunks: {
        cacheGroups: {
          vendored: {
            chunks: "initial",
            test: /\/node_modules\//u,
            maxSize: 4 * 1024 * 1024,
            name: "vendor",
            priority: -10,
          },
          shared: {
            chunks: "initial",
            // NOTE: this number was found empirically.
            // this chunk includes modules that are shared by 20 endpoints,
            // which is approximately 20% of the endpoints
            // rather keep this number static for now and adjust for performance later if needed
            minChunks: 20,
            name: "common",
            priority: -20,
            reuseExistingChunk: true,
          },
        },
      },
    },
    plugins: _.filter([
      new webpack.DefinePlugin({
        "process.env.NODE_DOMAIN": JSON.stringify("client"),
      }),
      new webpack.ProvidePlugin({
        // bootstrap requires a global jQuery definition
        $: "jquery",
        Buffer: [require.resolve("buffer/"), "Buffer"],
        jQuery: "jquery",
        process: require.resolve("process/browser"),
      }),
      clientSideSourceMapPlugin,
      entryWatcher,
      new MiniCssExtractPlugin({
        chunkFilename: emittedAssetName("chunk/[id].css"),
        filename: emittedAssetName("js/pages/[name].css"),
        ignoreOrder: true,
      }),
      new ManifestPlugin({
        fileName: path.join(webArtifactsDir, "server", manifestName),
        generate(manifest, files, entrypoints) {
          return _.extend(
            manifest,
            _.mapObject(entrypoints, (entryFiles) =>
              _.chain(entryFiles)
                .filter((file) => !/\.hot-update\./u.test(file))
                .map((file) => `${publicPath}${file}`)
                .flatten()
                .value(),
            ),
          );
        },
      }),
      development &&
        (() => {
          const ReactRefreshWebpackPlugin = require("@pmmmwh/react-refresh-webpack-plugin");
          return new ReactRefreshWebpackPlugin();
        })(),
    ]),
    module: {
      rules: _.flatten([
        {test: /\.m?js$/u, resolve: {fullySpecified: false}},
        babelLoader(development ? ["react-refresh/babel"] : []),
        clientSidePageLoader,
        mustacheLoader,
        rawLoader,
        clientSideStyleLoaders,
        assetLoader(),
      ]),
    },
  });
};
