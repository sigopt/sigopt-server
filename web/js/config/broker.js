/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import fs from "fs";
import jsonMergePatch from "json-merge-patch";
import path from "path";
import {parse as parseYAML} from "yaml";

import EnvironmentSource from "./env";
import ObjectSource from "./object";
import {
  coalesce,
  isDefinedAndNotNull,
  isJsObject,
  isUndefinedOrNull,
} from "../utils";

class ConfigBroker {
  constructor(sources) {
    this._sources = sources;
  }

  static fromFile(config) {
    const sources = [];
    let extend = config;
    while (isDefinedAndNotNull(extend)) {
      extend = path.resolve(extend);
      const data = parseYAML(fs.readFileSync(extend).toString());
      const original = extend;
      extend = data.extends;
      delete data.extends;
      sources.push(new ObjectSource(data));
      if (isDefinedAndNotNull(extend)) {
        let basedir = process.env.sigopt_server_config_dir || "./config";
        if (extend.startsWith("./") || extend.startsWith("../")) {
          basedir = path.dirname(original);
        }
        extend = path.join(basedir, extend);
      }
    }
    sources.push(new EnvironmentSource());
    return new ConfigBroker(sources);
  }

  initialize(success, error) {
    const init = ([head, ...tail]) => {
      if (head) {
        return head.initialize(_.partial(init, tail), error);
      } else {
        return success();
      }
    };
    init(this._sources);
  }

  get(key, defaultValue = undefined) {
    return this._ensureSafeReturn(
      coalesce(
        _.reduce(
          this._sources,
          (memo, source) => (isUndefinedOrNull(memo) ? source.get(key) : memo),
          undefined,
        ),
        defaultValue,
      ),
    );
  }

  _ensureSafeReturn(value) {
    if (isJsObject(value)) {
      throw new Error(
        "Possibly unsafe .get of JSON object, values might be missing." +
          " Please use .getObject instead",
      );
    }
    return value;
  }

  getObject(key, defaultValue = undefined) {
    const values = _.without(
      _.map(this._sources, (source) => source.get(key)),
      undefined,
    );
    if (_.isEmpty(values)) {
      return defaultValue;
    }
    values.reverse();
    return _.reduce(values, jsonMergePatch.apply, {});
  }

  allConfigsForLogging() {
    return _.map(this._sources, (source) => source.allConfigsForLogging());
  }
}

export default ConfigBroker;
