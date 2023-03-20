/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Poller from "../poller";

class AlwaysVisibleMonitor {
  addHandler(handler) {
    this.handler = handler;
    handler(true);
  }

  setVisible(visible) {
    this.handler(visible);
  }
}

class NeverVisibleMonitor {
  addHandler(handler) {
    handler(false);
  }
}

describe("Poller", function () {
  const poll = jest.fn();
  const error = jest.fn();
  const onChange = jest.fn();
  const visibilityMonitor = new AlwaysVisibleMonitor();
  const waitTime = 100;
  const makePoller = (opts) =>
    new Poller(
      _.extend({poll, error, onChange, visibilityMonitor, waitTime}, opts),
    );

  beforeEach(function () {
    poll.mockReset();
    error.mockReset();
    onChange.mockReset();
  });

  it("waits to poll", function () {
    makePoller();
    expect(error.mock.calls).toEqual([]);
    expect(poll.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toEqual([]);
  });

  it("can be started", function () {
    makePoller().startOnce();
    expect(poll.mock.calls).toHaveLength(1);
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toEqual([]);
  });

  it("can return results", function () {
    makePoller().startOnce();
    const triggerSuccess = poll.mock.calls[0][0];
    const result = [1, 2, 3];
    triggerSuccess(result);
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toEqual([[result]]);
  });

  it("handles errors", function () {
    makePoller().startOnce();
    const triggerError = poll.mock.calls[0][1];
    const exception = [3, 2, 1];
    triggerError(exception);
    expect(error.mock.calls).toEqual([[exception]]);
    expect(onChange.mock.calls).toEqual([]);
  });

  it("can be stopped", function () {
    makePoller().startOnce().stop();
    const triggerSuccess = poll.mock.calls[0][0];
    triggerSuccess();
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toEqual([]);
  });

  it("can only be started once", function () {
    makePoller().startOnce().stop().startOnce();
    const triggerSuccess = poll.mock.calls[0][0];
    triggerSuccess();
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toEqual([]);
  });

  it("can be paused", function () {
    makePoller().setPaused(true).startOnce();
    expect(poll.mock.calls).toEqual([]);
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toEqual([]);
  });

  it("receives results while paused", function () {
    makePoller().startOnce().setPaused(true);
    const triggerSuccess = poll.mock.calls[0][0];
    triggerSuccess();
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toHaveLength(1);
  });

  it("wont start when backgrounded", function () {
    makePoller({visibilityMonitor: new NeverVisibleMonitor()}).startOnce();
    expect(poll.mock.calls).toEqual([]);
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toEqual([]);
  });

  it("wont start when set not visible", function () {
    const poller = makePoller();
    visibilityMonitor.setVisible(false);
    poller.startOnce();
    expect(poll.mock.calls).toEqual([]);
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toEqual([]);
  });

  it("pauses when backgrounded", function () {
    makePoller().startOnce();
    visibilityMonitor.setVisible(false);
    const triggerSuccess = poll.mock.calls[0][0];
    triggerSuccess();
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toHaveLength(1);
  });

  it("doesnt start on its own", function () {
    makePoller();
    visibilityMonitor.setVisible(true);
    expect(poll.mock.calls).toEqual([]);
    expect(error.mock.calls).toEqual([]);
    expect(onChange.mock.calls).toEqual([]);
  });
});
