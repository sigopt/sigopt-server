/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import natCompare from "natural-compare-lite";

export default function (a, b) {
  return natCompare(a.name, b.name);
}
