/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Endpoint from "../../server/endpoint/base";
import {SicknessError} from "../../net/errors";

export default class SicknessEndpoint extends Endpoint {
  parseParams() {
    return Promise.reject(new SicknessError());
  }
}
