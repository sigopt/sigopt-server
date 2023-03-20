/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import getSettings from "./settings";
import getUnusedCodeConfig from "./unused_code_config";

export default (env = {}) => {
  return getSettings(env).then((settings) => getUnusedCodeConfig(settings));
};
