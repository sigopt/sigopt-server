/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ChartLineGlyph from "../../component/glyph/chart-line";
import CheckGlyph from "../../component/glyph/check";
import CircleExclamationGlyph from "../../component/glyph/circle-exclamation";

export const statusGlyphs = {
  completed: CheckGlyph,
  failed: CircleExclamationGlyph,
  active: ChartLineGlyph,
};

export const XGBOOST = "XGBoost";
export const HYPEROPT = "hyperopt";
