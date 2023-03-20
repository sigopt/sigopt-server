/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import BaseAlertBroker from "../../alert/base";

export default class CollectingAlertBroker extends BaseAlertBroker {
  constructor(services) {
    super(services);
    this.alerts = [];
  }

  handle(lert) {
    lert.handle();
    this.alerts.push(lert);
  }

  clearAlerts() {
    this.alerts = [];
  }

  getAlerts() {
    return this.alerts;
  }
}
