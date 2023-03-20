/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

// Alerts go through the AlertBroker.
//
// If a page wants to render alerts in a custom manner, then they can register a
// handler. Then for each new alert their handler will be called with that Alert
// as an argument and it can be handled however the page wants.
//
// If there are no custom handlers, then Alerts are rendered in a default manner.

import $ from "jquery";
import _ from "underscore";
import React from "react";
import ReactDOM from "react-dom";
import smoothscroll from "smoothscroll";

import AlertPanel from "./panel";
import BaseAlertBroker from "./base";

export default class AlertBroker extends BaseAlertBroker {
  constructor(services) {
    super(services);
    this._handlerQueue = [this.defaultHandler];
  }

  handle(lert) {
    this._handlerQueue[0](lert);
    if (lert) {
      lert.handle();
    }
  }

  hasRegisteredHandler(handler) {
    return this._handlerQueue[0] === handler;
  }

  registerHandler(handler) {
    this._handlerQueue.unshift(handler);
  }

  releaseHandler(handler) {
    if (this.hasRegisteredHandler(handler)) {
      this._handlerQueue.shift();
    }
  }

  defaultHandler(lert) {
    const div = document.createElement("div");
    const flashBox = $("#flash-box").toArray()[0];
    flashBox.append(div);

    if (lert) {
      ReactDOM.render(<AlertPanel error={lert} />, div);
      smoothscroll(0);
    } else {
      _.map(flashBox.children, (child) =>
        ReactDOM.unmountComponentAtNode(child),
      );
    }
  }

  clearAlerts = () => this.handle(null);
}
