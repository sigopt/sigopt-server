/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import appRoutes from "./routes/app";

export default function make(configBroker) {
  return appRoutes(configBroker);
}
