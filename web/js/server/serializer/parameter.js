/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {SerializeableForClientBundle} from "../../services/base";
import {isJsObject} from "../../utils";

export default class ParameterSerializer {
  serialize(params) {
    if (params instanceof SerializeableForClientBundle) {
      return this.serialize(params.serializeAs());
    }
    if (_.isArray(params)) {
      return _.map(params, (value) => this.serialize(value));
    }
    if (isJsObject(params)) {
      return _.mapObject(params, (value) => this.serialize(value));
    }
    return params;
  }
}
