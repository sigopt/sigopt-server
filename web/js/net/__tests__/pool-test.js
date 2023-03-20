/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import SourcePool from "../pool";

describe("it pools", () => {
  it("handles a single arg", () => {
    const fakeHandler = jest.fn();
    const pool = new SourcePool(fakeHandler);
    const arg1 = 1;
    const arg2 = 2;
    const return1 = 3;
    const return2 = 4;

    fakeHandler.mockReturnValueOnce(return1);
    fakeHandler.mockReturnValueOnce(return2);

    expect(pool.get(arg1)).toBe(return1);
    expect(pool.get(arg2)).toBe(return2);
    expect(pool.get(arg1)).toBe(return1);
    expect(pool.get(arg2)).toBe(return2);
  });

  it("handles an object as an arg", () => {
    const fakeHandler = jest.fn();
    const pool = new SourcePool(fakeHandler);
    const arg1 = {x: "1"};
    const arg2 = {x: "2"};
    const return1 = 3;
    const return2 = 4;

    fakeHandler.mockReturnValueOnce(return1);
    fakeHandler.mockReturnValueOnce(return2);

    expect(pool.get(arg1)).toBe(return1);
    expect(pool.get(arg2)).toBe(return2);
    expect(pool.get(arg1)).toBe(return1);
    expect(pool.get(arg2)).toBe(return2);
  });

  it("handles multiple complex arguments", () => {
    const fakeHandler = jest.fn();
    const pool = new SourcePool(fakeHandler);
    const args1 = [{x: "1"}, "waffles", 8, undefined, null];
    const args2 = [{x: "2"}, ["oh o", {nesting: {gone: {crazy: 3}}}]];
    const return1 = 3;
    const return2 = 4;

    fakeHandler.mockReturnValueOnce(return1);
    fakeHandler.mockReturnValueOnce(return2);

    expect(pool.get(...args1)).toBe(return1);
    expect(fakeHandler.mock.calls[0]).toEqual(args1);
    expect(pool.get(...args2)).toBe(return2);
    expect(fakeHandler.mock.calls[1]).toEqual(args2);
    expect(pool.get(...args1)).toBe(return1);
    expect(pool.get(...args2)).toBe(return2);
  });

  it("throws if args can't be safely memoized", () => {
    const fakeHandler = jest.fn();
    const pool = new SourcePool(fakeHandler);
    const testValues = [NaN, new Map(), Math, () => 1, Infinity];

    _.map(testValues, (testvalue) => {
      expect(() => {
        pool.get(testvalue);
      }).toThrow();
    });
  });
});
