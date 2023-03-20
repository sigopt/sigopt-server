/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Service from "../services/base";
import SigoptError from "../error/base";

/* eslint-disable no-console */

export const PYTHON_LOG_LEVELS = {
  error: 40,
  warn: 30,
  info: 20,
  debug: 10,
};

const LOG_LEVEL_NAMES = _.invert(PYTHON_LOG_LEVELS);

const realConsoleError = console.error;

class Logger {
  constructor(options) {
    this.name = options.name;
    this.level = options.level;
  }

  log(level, ...args) {
    if (level >= this.level) {
      const output =
        {
          50: console.error,
          40: console.error,
          30: console.error,
          20: console.log,
          10: console.log,
        }[level] || console.log;
      const loggerName = this.name;
      const renderedLevel = LOG_LEVEL_NAMES[level] || level.toString();
      const timestamp = new Date().toISOString();
      output.call(console, timestamp, renderedLevel, loggerName, ...args);
    }
  }
}

export class LoggingService extends Service {
  constructor(services, options) {
    super(services, options);
    this._maybeEnableFatalErrors();
    this.rootLogger = new Logger({name: "root", level: 20});
    this.loggers = _.mapObject(
      options.levels,
      (level, name) => new Logger({name, level}),
    );
  }

  info(logger, ...args) {
    this._log(PYTHON_LOG_LEVELS.info, logger, ...args);
  }

  error(logger, ...args) {
    this._log(PYTHON_LOG_LEVELS.error, logger, ...args);
  }

  _maybeEnableFatalErrors() {
    const fatalErrors = this.options.warnings === "error";
    const errorHandler = fatalErrors
      ? function (...args) {
          const thrown = _.isError(args[0])
            ? new SigoptError().chain(args[0])
            : new Error(args[0]);
          realConsoleError(thrown, ...args.slice(1));
        }
      : realConsoleError;
    console.error = errorHandler;
    console.warn = errorHandler;
  }

  _log(level, loggerName, ...args) {
    const [logger, logArgs] = _.isEmpty(args)
      ? [this.rootLogger, [loggerName]]
      : [this.loggers[loggerName] || this.rootLogger, args];
    logger.log(level, ...logArgs);
  }
}

export default class ClientLoggingService extends LoggingService {}
