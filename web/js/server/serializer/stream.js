/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Serializer from "./base";

export default class StreamResponseSerializer extends Serializer {
  serialize(req, res, endpointParams, endpointResponse) {
    return Promise.resolve(endpointResponse.body).then(
      (body) =>
        new Promise((success, error) => {
          body.on("end", success);
          body.on("error", error);
          body.pipe(res);
        }),
    );
  }
}
