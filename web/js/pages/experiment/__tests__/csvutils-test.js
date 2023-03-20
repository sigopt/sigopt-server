/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {excelSanitize, excelUnsanitize} from "../csvutils";

describe("csvutils", () => {
  it.each([
    "",
    "abc",
    "   abc",
    "=def",
    " =1+1",
    "@123",
    " @456",
    "       @789",
    "-",
    "-1.2",
    " -2.2",
    "     -3.2",
    "+",
    "+1.2",
    " +2.2",
  ])("should sanitize %s safely", (arg) => {
    const sanitized = excelSanitize(arg);
    expect(sanitized.charAt(0)).not.toEqual("=");
    expect(sanitized.charAt(0)).not.toEqual("-");
    expect(sanitized.charAt(0)).not.toEqual("+");
    expect(sanitized.charAt(0)).not.toEqual("@");
    expect(excelUnsanitize(excelSanitize(arg))).toEqual(arg);
  });

  it("should not modify manually-entered input", () => {
    expect(excelUnsanitize("")).toEqual("");
    expect(excelUnsanitize("  ")).toEqual("  ");
    expect(excelUnsanitize("  abc")).toEqual("  abc");
    expect(excelUnsanitize("@")).toEqual("@");
    expect(excelUnsanitize("=123")).toEqual("=123");
    expect(excelUnsanitize("-1.23")).toEqual("-1.23");
  });

  it.each([1, null, undefined, false])("should ignore non-string %s", (arg) => {
    expect(excelSanitize(arg)).toBe(arg);
    expect(excelUnsanitize(arg)).toBe(arg);
  });
});
