/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import HistoryTracker from "../../net/history";

describe("historyTracker", () => {
  const initialStateArgs = "test";

  it("doesn't error without handlers", function () {
    const tracker = new HistoryTracker();

    tracker.pushState({}, null);

    expect(_.isEmpty(tracker.handlers)).toBe(true);
  });

  it("properly adds multiple handlers", function () {
    const tracker = new HistoryTracker();

    tracker.addHandler("handler1", () => "doing nothing", initialStateArgs);
    tracker.addHandler("handler2", () => "doing nothing", initialStateArgs);
    tracker.addHandler("handler3", () => "doing nothing", initialStateArgs);
    tracker.addHandler("handler4", () => "doing nothing", initialStateArgs);

    expect(Object.keys(tracker.handlers)).toHaveLength(4);
    expect(Object.keys(tracker.initialStateArgs)).toHaveLength(4);
    expect(Object.keys(tracker.lastState)).toHaveLength(4);
  });

  it("deals with duplicate keys", function () {
    const tracker = new HistoryTracker();

    tracker.addHandler("duplicateKey", () => "doing nothing", initialStateArgs);
    tracker.addHandler("duplicateKey", () => "doing nothing", initialStateArgs);

    expect(Object.keys(tracker.handlers)).toHaveLength(1);
    expect(Object.keys(tracker.initialStateArgs)).toHaveLength(1);
    expect(Object.keys(tracker.lastState)).toHaveLength(1);
  });

  it("deals with duplicate handlers", function () {
    const tracker = new HistoryTracker();
    const genericHandler = function () {
      return "doing nothing";
    };

    tracker.addHandler("duplicateHandler1", genericHandler, initialStateArgs);
    tracker.addHandler("duplicateHandler2", genericHandler, initialStateArgs);

    expect(Object.keys(tracker.handlers)).toHaveLength(1);
    expect(Object.keys(tracker.initialStateArgs)).toHaveLength(1);
    expect(Object.keys(tracker.lastState)).toHaveLength(1);
  });
});
