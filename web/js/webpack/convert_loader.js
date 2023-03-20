/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {getOptions} from "loader-utils";

export default (loader) =>
  function (source, map, meta) {
    return this.callback(
      null,
      loader(source, this.resourcePath, getOptions(this)),
      map,
      meta,
    );
  };
