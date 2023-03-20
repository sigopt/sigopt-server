/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {ConfigBrokerValueNotAvailableException} from "./exceptions";
import {NOT_AVAILABLE} from "./constants";

const dottedNameParts = (key) => key.split(".");
const dottedNamePrefix = (key) => _.initial(dottedNameParts(key));
const dottedNameSuffix = (key) => _.last(dottedNameParts(key));

const containsNotAvailable = (val) => {
  if (val === NOT_AVAILABLE) {
    return true;
  } else if (_.isArray(val)) {
    return _.any(val, containsNotAvailable);
  } else if (_.isObject(val)) {
    return containsNotAvailable(_.values(val));
  } else {
    return false;
  }
};

const getDottedNameFromObject = (object, key) => {
  const prefix = dottedNamePrefix(key);
  const suffix = dottedNameSuffix(key);
  const parentObject = _.reduce(
    prefix,
    (memo, part) => {
      if (memo === NOT_AVAILABLE) {
        return memo;
      }
      return memo[part] || {};
    },
    object,
  );
  const value =
    parentObject === NOT_AVAILABLE ? NOT_AVAILABLE : parentObject[suffix];
  if (containsNotAvailable(value)) {
    throw new ConfigBrokerValueNotAvailableException(key);
  }
  return value;
};

const setDottedNameFromObject = (object, key, value) => {
  const prefix = dottedNamePrefix(key);
  const suffix = dottedNameSuffix(key);
  const base = _.reduce(
    prefix,
    (memo, part) => {
      memo[part] = memo[part] || {};
      if (memo[part] === NOT_AVAILABLE) {
        throw new ConfigBrokerValueNotAvailableException(key);
      }
      return memo[part];
    },
    object,
  );
  base[suffix] = value;
};

export default class ObjectSource {
  constructor(obj) {
    this._config = obj;
  }

  initialize(success) {
    success();
  }

  get(key) {
    return getDottedNameFromObject(this._config, key);
  }

  setNotAvailable(key) {
    setDottedNameFromObject(this._config, key, NOT_AVAILABLE);
  }

  allConfigsForLogging() {
    return this._config;
  }
}
