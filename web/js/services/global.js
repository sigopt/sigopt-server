/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import EntryManifest from "../render/entry_manifest";
import WinstonLoggingService from "../log/winston";

export default class GlobalServiceBag {
  constructor(configBroker, entryManifestFile) {
    this.configBroker = configBroker;

    this.entryManifest = new EntryManifest(this, {entryManifestFile});
    this.winstonLogger = new WinstonLoggingService(this, {
      environment: configBroker.get("logging.environment"),
    });
  }

  warmup() {
    /* eslint-disable no-console */
    return Promise.resolve(null)
      .then(() => this.entryManifest.warmup())
      .then(() => this.winstonLogger.warmup())
      .then(() => this);
    /* eslint-enable no-console */
  }
}
