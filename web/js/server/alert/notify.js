/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Service from "../../services/base";

export default class NoopAlertNotifier extends Service {
  cleanupError() {
    // no-op
  }
}
