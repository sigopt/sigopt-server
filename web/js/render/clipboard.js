/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export default process.env.NODE_DOMAIN === "server"
  ? null
  : require("clipboard");
