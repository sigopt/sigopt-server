/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import crypto from "crypto";

import {headCodeString} from "./head_js";

export const headCodeHash = crypto
  .createHash("sha512")
  .update(headCodeString)
  .digest("base64");
