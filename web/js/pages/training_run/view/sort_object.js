/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {naturalStringCompare} from "../../../utils";

export default (obj) =>
  _.chain(obj)
    .pairs()
    .sort(([key1], [key2]) => naturalStringCompare(key1, key2))
    .value();
