/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import * as utils from "../utils";

describe("utils", () => {
  describe("promiseFinally", () => {
    it("handles resolved promises", (done) => {
      const final = jest.fn();
      const promise = new Promise((s) => {
        expect(final.mock.calls).toHaveLength(0);
        s();
      });
      utils
        .promiseFinally(promise, final)
        .catch(() => done.fail())
        .then(() => {
          expect(final.mock.calls).toHaveLength(1);
          done();
        })
        .catch(done.fail);
    });

    it("handles rejected promises", (done) => {
      const final = jest.fn();
      const promise = new Promise((s, e) => {
        expect(final.mock.calls).toHaveLength(0);
        e(new Error());
      });
      utils
        .promiseFinally(promise, final)
        .then(() => done.fail())
        .catch(() => {
          expect(final.mock.calls).toHaveLength(1);
          done();
        });
    });
  });

  it("handles strings", () => {
    const cases = [
      ["", ""],
      ["", "abc"],
      ["abc", ""],
      ["abc", "a"],
      ["abc", "b"],
      ["abc", "c"],
      ["a", "abc"],
      ["b", "abc"],
      ["c", "abc"],
      ["aaaabc", "a"],
      ["aaaabc", "aaa"],
      ["aaaabc", "aaaaaa"],
      ["abcccc", "c"],
      ["abcccc", "ccc"],
      ["abcccc", "cccccc"],
    ];
    _.each(cases, ([base, search]) => {
      expect(utils.startsWith(base, search)).toEqual(base.startsWith(search));
    });
  });

  describe("colorHexToRGB", () => {
    _.map(
      [
        ["#000000", 0x00, 0x00, 0x00],
        ["#123456", 0x12, 0x34, 0x56],
        ["#abcdef", 0xab, 0xcd, 0xef],
        ["#ABCDEF", 0xab, 0xcd, 0xef],
        ["#1a2B3c", 0x1a, 0x2b, 0x3c],
      ],
      ([color, r, g, b]) => {
        it(`parses the color ${color} correctly`, () => {
          const parsed = utils.colorHexToRGB(color);
          expect(parsed).toEqual({r, g, b});
        });
      },
    );
    _.map(
      ["", "#", "#0", "#000", "#0000", "#00000", "#0000000", "#COLOUR", "red"],
      (color) => {
        it(`throws when parsing ${color}`, () => {
          const parse = () => utils.colorHexToRGB(color);
          expect(parse).toThrow();
        });
      },
    );
  });
});
