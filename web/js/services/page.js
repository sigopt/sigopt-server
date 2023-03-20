/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import $ from "jquery";

import ClientServiceBag from "./client";

let serviceBag = null;

export default function getServicesFromPage(callback) {
  $(document).ready(function () {
    if (serviceBag === null) {
      const serviceArgs = JSON.parse($("#service-args").text());
      serviceBag = new ClientServiceBag(serviceArgs);
    }
    callback(serviceBag);
  });
}
