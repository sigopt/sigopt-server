/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import getServerSideConfig from "./server_side_config";
import getSettings from "./settings";

export default (env = {}) => {
  return getSettings(env).then((settings) => getServerSideConfig(settings));
};
