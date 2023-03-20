/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import $ from "jquery";
import _ from "underscore";

import getServicesFromPage from "./services/page";
import inflateServices from "./services/inflate";
import {INIT_CSP_ERROR_LOCATION} from "./chrome/head_js";

export default function (callback) {
  getServicesFromPage(function (services) {
    window.addEventListener("unhandledrejection", (event) => {
      services.errorNotifier.cleanupError(event.reason);
    });

    _.map(window[INIT_CSP_ERROR_LOCATION], (event) => {
      services.errorNotifier.cleanupError(event);
    });

    window.addEventListener("securitypolicyviolation", (event) => {
      services.errorNotifier.cleanupError(event);
    });

    $(document).ready(function () {
      const args = inflateServices(
        JSON.parse($("#page-args").text()),
        services,
      );
      callback(args);
    });
  });
}
