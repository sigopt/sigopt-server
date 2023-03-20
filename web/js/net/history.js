/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {isDefinedAndNotNull} from "../utils";

// Keeps track of a page's history
// Fires the registered handlers when the back or forward button is clicked
class HistoryTracker {
  constructor() {
    this.handlers = {};
    this.initialStateArgs = {};
    // The last state seen by the user
    this.lastState = {};
  }

  _isHandlerValid(key, handler) {
    const duplicate = _.find(
      _.keys(this.handlers),
      (k) => k === key || this.handlers[k] === handler,
    );
    return !isDefinedAndNotNull(duplicate);
  }

  // Adds a handler and the component's initial state identified by a unique key
  // Each component that is to be tracked should be registered with
  // it's own handler, initial state, current state and viewed state
  addHandler(key, handler, initialStateArgs) {
    if (this._isHandlerValid(key, handler)) {
      if (_.isEmpty(this.handlers)) {
        this._startTracking();
      }
      this.handlers[key] = handler;
      this.initialStateArgs[key] = initialStateArgs;
      this.lastState[key] = initialStateArgs;
    }
  }

  // Pushes a hashmap of component states corresponding to the unique key
  // to the window's history stack
  pushState(stateObj, url) {
    _.extend(this.lastState, stateObj);
    window.history.pushState(this.lastState, null, url);
  }

  _startTracking() {
    window.addEventListener("popstate", (e) => {
      this._basePopHandler(e);
    });
  }

  _basePopHandler(e) {
    // e.state is the state of the page AFTER the back or forward button is pressed.
    // We check whether the state has changed by comparing e.state with the lastState and call handlers if changed
    // Then we update the last state with e.state
    if (isDefinedAndNotNull(e.state)) {
      _.map(_.keys(e.state), (key) => {
        if (e.state[key] !== this.lastState[key]) {
          this.handlers[key](e.state[key]);
        }
      });
      this.lastState = e.state;
    } else {
      // If the stack is empty, the page has reached the initial state
      // and the browser will pop a null state object
      _.map(_.keys(this.initialStateArgs), (key) => {
        if (this.initialStateArgs[key] !== this.lastState[key]) {
          this.handlers[key](this.initialStateArgs[key]);
        }
      });
      this.lastState = this.initialStateArgs;
    }
  }

  setBrowserUrl(url) {
    window.history.replaceState(window.history.state, null, url);
  }
}

export default HistoryTracker;
