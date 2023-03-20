/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {HYPEROPT, XGBOOST} from "./constants";

const XGB_INTEGRATION_KEYWORD = "_IS_XGB_RUN";

export const GetTrainingRunIntegrationType = (run) => {
  if (XGB_INTEGRATION_KEYWORD in run.dev_metadata) {
    return XGBOOST;
  }
  if (run.metadata && run.metadata.optimizer === HYPEROPT) {
    return HYPEROPT;
  }
  return "";
};
