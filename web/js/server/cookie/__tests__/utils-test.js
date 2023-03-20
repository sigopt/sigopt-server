/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {isUrlSafeBase64} from "url-safe-base64";

import {S3_SAFE_REGEX} from "../constants";
import {newRandomCookieId} from "../utils";

const repeat = (fun) => {
  _.each(_.range(64), () => fun());
};

describe("newRandomCookieId", () => {
  it("uses url safe padding", () => {
    repeat(() => {
      expect(newRandomCookieId().slice(-2)).toBe("..");
    });
  });

  it("encodes url safe IDs", () => {
    repeat(() => {
      expect(isUrlSafeBase64(newRandomCookieId())).toBe(true);
    });
  });

  it("encodes S3 safe IDs", () => {
    repeat(() => {
      expect(newRandomCookieId()).toMatch(S3_SAFE_REGEX);
    });
  });
});
