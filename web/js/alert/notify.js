/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Service from "../services/base";

const CSPErrorFormatter = (event) => {
  return JSON.stringify(
    _.pick(event, [
      "sourceFile",
      "documentURI",
      "violatedDirective",
      "blockedURI",
    ]),
  );
};

const CSPErrorShouldIgnore = (event) => {
  const ignoreSourceFiles = [
    "moz-extension",
    "sandbox eval code",
    "chrome-extension",
    "user-script",
  ];

  return _.contains(ignoreSourceFiles, event.sourceFile);
};

class ErrorNotifier extends Service {
  cleanupError(error) {
    if (error && !error.hasBeenHandled) {
      let exception = error.exception || error.message || error;

      if (error.type === "securitypolicyviolation") {
        if (CSPErrorShouldIgnore(error)) {
          return;
        }
        exception = CSPErrorFormatter(error);
      }

      // XMLHttpRequests have readyStates representing the stages of the
      // request - 0 means that the request was not initialized.  This
      // indicates the fault of the local environment (browser, internet
      // connection) rather than our API having an actual error.
      const readyState = error.jqXhr && error.jqXhr.readyState;
      if (readyState !== 0) {
        // eslint-disable-next-line no-console
        console.error(exception, {
          status: error.status,
          request: error.request,
          response: error.responseText,
        });
        this.services.alertBroker.show(exception);
      }
    }
  }
}

export default ErrorNotifier;
