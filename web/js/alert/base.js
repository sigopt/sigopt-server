/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Alert from "./alert";
import Service from "../services/base";

export default class BaseAlertBroker extends Service {
  constructor(services) {
    super(services);
    this.handler = this.defaultHandler;
  }

  handle(lert) {
    this.handler(lert);
    if (lert) {
      lert.handle();
    }
  }

  show(message, type = "danger") {
    this.handle(new Alert({message: message, type: type}));
  }

  info(message) {
    this.show(message, "info");
  }

  // Returns an error handler that handles errors if they match the expected
  // status code
  errorHandlerThatExpectsStatus(...statuses) {
    return (e) => {
      if (e && e.status && _.contains(statuses, e.status)) {
        this.handle(e);
        return Promise.resolve();
      } else {
        return Promise.reject(e);
      }
    };
  }
}
