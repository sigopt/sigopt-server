/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {coalesce} from "../utils";

// Detects changes to the page's visibilty.
// Useful for starting/stopping events when the page
// is backgrounded or hidden.
//
// Uses the page visibility API, which is documented at
// https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API
class VisibilityMonitor {
  constructor() {
    this.handlers = [];
    const eventName = this._getHiddenApiNames()[1];
    document.addEventListener(eventName, () => this._ourHandler(), false);
  }

  addHandler(handler) {
    this.handlers.push(handler);
    this._ourHandler();
  }

  _ourHandler() {
    const isVisible = !this._pageIsHidden();
    _.each(this.handlers, (h) => h(isVisible));
  }

  _pageIsHidden() {
    const attributeName = this._getHiddenApiNames()[0];
    const hidden = attributeName && document[attributeName];
    return coalesce(hidden, false);
  }

  _getHiddenApiNames() {
    if (typeof document.hidden === "boolean") {
      return ["hidden", "visibilitychange"];
    } else if (typeof document.mozHidden === "boolean") {
      return ["mozHidden", "mozvisibilitychange"];
    } else if (typeof document.msHidden === "boolean") {
      return ["msHidden", "msvisibilitychange"];
    } else if (typeof document.webkitHidden === "boolean") {
      return ["webkitHidden", "webkitvisibilitychange"];
    } else {
      return [undefined, undefined];
    }
  }
}

export default VisibilityMonitor;
