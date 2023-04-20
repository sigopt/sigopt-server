/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {ConfigBroker} from "sigopt-config";

import Service from "../services/base";
import {coalesce} from "../utils";

export default class ClientsideConfigBrokerService extends Service {
  constructor(services, options) {
    super(services, options);
    this._source = new ConfigBroker(options);
  }

  get(key, defaultValue = undefined) {
    return coalesce(this._source.get(key), defaultValue);
  }

  serializeAs() {
    return this.options;
  }
}
