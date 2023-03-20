/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export default function escapeForScriptTag(text) {
  return {
    __html: text
      .replace(/\u2028/gu, "\\u2028")
      .replace(/\u2029/gu, "\\u2029")
      .replace(/</gu, "\\u003c"),
  };
}
