/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Serializer from "./base";

export default class JsonSerializer extends Serializer {
  serialize(req, res, endpointParams, endpointResponse) {
    res.send(JSON.stringify(endpointResponse.body));
  }
}
