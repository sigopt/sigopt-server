/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Alert from "../../alert/alert";
import ReactEndpoint from "../../server/endpoint/react";
import {HttpError, SicknessError} from "../../net/errors";

export default class ErrorEndpoint extends ReactEndpoint {
  constructor(status, error) {
    super();
    this.status = status;
    this.error = error;
  }

  static page = require("./page");

  pageName() {
    return (
      {
        400: "Bad Request",
        404: "Content Not Found",
      }[this.status] || "Internal Server Error"
    );
  }

  parseParams(req) {
    const error = this.error;
    const errorMessage =
      error instanceof Alert || error instanceof HttpError
        ? error.message
        : null;
    return Promise.resolve({
      errorMsg: errorMessage,
      loggedIn: Boolean(req.currentUser),
      loginState: req.loginState,
      path: req.path,
      showTestError: this.error instanceof SicknessError,
      status: this.status,
    });
  }
}
