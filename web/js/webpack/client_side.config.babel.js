/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import getClientSideConfig from "./client_side_config";
import getSettings from "./settings";

export default (env = {}) => {
  return getSettings(env).then((settings) => getClientSideConfig(settings));
};
