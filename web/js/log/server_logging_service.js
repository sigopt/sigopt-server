/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {LoggingService} from "./client_logging_service";

export const sendToWinston = (globalServices, level, loggerName, logJson) => {
  const environment =
    globalServices &&
    globalServices.winstonLogger &&
    globalServices.winstonLogger.environment;
  const syslogLevel =
    {
      50: "crit",
      40: "error",
      30: "warning",
      20: "info",
      10: "debug",
    }[level] || "info";

  globalServices.winstonLogger.log(
    _.extend(
      {
        environment, // TODO(SN-1160): Can this be added automatically?
        level: syslogLevel,
        loggerName,
      },
      logJson,
    ),
  );
};

export class ServerLoggingService extends LoggingService {
  syslog(level, loggerName, ...args) {
    if (level && loggerName && !_.isEmpty(args)) {
      sendToWinston(this.services.globalServices, level, loggerName, {
        message: args,
      });
    }
  }

  _log(level, loggerName, ...args) {
    /* eslint no-underscore-dangle: ["error", { "allowAfterSuper": true }] */
    super._log(level, loggerName, ...args);
    this.syslog(level, loggerName, ...args);
  }
}
