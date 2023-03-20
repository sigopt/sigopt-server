/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import VisibilityMonitor from "./visibility";

// Polls an external source repeatedly, searching for changes.
// The `onChange` function is called when there is new data to report.
class Poller {
  /**
   * @param {{
   *   error: function(*),
   *   poll: function(function(*)=, function(*)=),
   *   onChange: function(*),
   *   visibilityMonitor: VisiblityMonitor,
   *   waitTime: number
   * }} options
   * @constructor
   */
  constructor(options) {
    this.poll = options.poll;
    this.error = options.error;
    this.onChange = options.onChange;
    this.waitTime = options.waitTime;

    this.lastData = null;
    this.isPolling = false;
    this.stopped = true;
    this.paused = false;

    this.visibilityMonitor =
      options.visibilityMonitor || new VisibilityMonitor();
    this.visibilityMonitor.addHandler((isVisible) =>
      this.setPaused(!isVisible),
    );

    this.startOnce = _.once(this.start);
    this.doPoll = _.throttle(() => {
      if (!this.isPolling && !this.stopped) {
        this.isPolling = true;
        this.poll(_.bind(this.pollSuccess, this), _.bind(this.pollError, this));
      }
    }, this.waitTime);
  }

  // When a Poller is paused, no new polls will be done, but existing polls
  // will continue
  setPaused(paused) {
    this.paused = paused;
    if (!this.paused) {
      this.nextPoll();
    }
    return this;
  }

  // When a Poller is stopped, no new polls will be done, and the results of
  // existing polls will be ignored
  start() {
    this.stopped = false;
    this.nextPoll();
    return this;
  }

  stop() {
    this.stopped = true;
    return this;
  }

  nextPoll() {
    if (!this.stopped && !this.paused) {
      this.doPoll();
    }
  }

  pollSuccess(newData) {
    this.isPolling = false;
    if (!this.stopped) {
      if (!_.isEqual(newData, this.lastData)) {
        this.onChange(newData);
      }
      this.lastData = newData;
      _.defer(() => this.nextPoll());
    }
  }

  pollError(...args) {
    this.isPolling = false;
    if (this.error) {
      this.error(...args);
    }
    _.defer(() => this.nextPoll());
  }
}

export default Poller;
