/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import toobusy from "toobusy-js";

import {TooBusyError} from "../../net/errors";

export default function tooBusy(req, res, next) {
  return next(toobusy() ? new TooBusyError() : null);
}
