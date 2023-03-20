/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import fs from "fs";

import Service from "../services/base";

export default class EntryManifest extends Service {
  loadedManifest = null;

  warmup() {
    if (process.env.NODE_ENV === "production") {
      // NOTE: cache the manifest in production because it is only expected to change across deploys
      // and we want this to fail before any requests are made
      this.loadedManifest = this.loadManifest();
    }
  }

  loadManifest() {
    const {entryManifestFile} = this.options;
    return JSON.parse(fs.readFileSync(entryManifestFile));
  }

  getAssets(entry) {
    const manifest = this.loadedManifest || this.loadManifest();
    const files = _.reject(manifest[entry], (f) => f.match(/\.map$/u));
    const [jsFiles, jsRest] = _.partition(files, (f) => f.match(/\.js$/u));
    if (_.isEmpty(jsFiles)) {
      throw new Error(`No javascript found for ${entry}`);
    }
    const [cssFiles, cssRest] = _.partition(jsRest, (f) => f.match(/\.css$/u));
    if (!_.isEmpty(cssRest)) {
      throw new Error(`Unhandled files ${cssRest}`);
    }
    return {css: cssFiles, js: jsFiles};
  }
}
