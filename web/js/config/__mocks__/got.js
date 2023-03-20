/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

class Got {
  get(url) {
    if (
      url === "http://169.254.169.254/latest/dynamic/instance-identity/document"
    ) {
      return Promise.resolve({
        instanceId: "i-03da972656e0adbbb",
        region: "us-west-2",
      });
    } else {
      return Promise.reject(new Error("ERROR"));
    }
  }
}

export default new Got();
