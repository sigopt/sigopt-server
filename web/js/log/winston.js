/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import transports from "winston-syslog";
import winston from "winston";

import Service from "../services/base";

export default class WinstonLoggingService extends Service {
  constructor(services, options) {
    super(services, options);
    this._logger = null;
  }

  get environment() {
    return this.options.environment;
  }

  warmup() {
    // NOTE: each winston logger creates a new socket connection that does not close until the node
    // process is restarted. So, the winston logger must be created once when the express app starts up
    // and not once per request in the ServerLoggingService.
    this._logger = winston.createLogger({
      format: winston.format.printf((info) => JSON.stringify(info)),
      levels: winston.config.syslog.levels,
      transports: [new transports.Syslog()],
    });
    return Promise.resolve(null);
  }

  log(...args) {
    return this._logger.log(...args);
  }
}
