/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const FONT_SIZE = 14;
export const TICK_FONT_SIZE = 12;

export const FONT_FAMILY = '"Metropolis", "Helvetica", "Arial", sans-serif';

export const PARAMETER_SOURCES = {
  SIGOPT: "SigOpt",
  XGBOOST_DEFAULTS: "XGBoost Defaults",
  USER: "User Specified",
};

export const AxisTypes = {
  PARAMETER: "parameter",
  METADATA: "metadata",
  CONDITIONAL: "conditional",
  TASK: "task",
  OPTIMIZED_METRIC: "optimized-metric",
  STORED_METRIC: "stored-metric",
  CONSTRAINED_METRIC: "constrained-metric",
};

export const CHART_COLORS = {
  LIGHT_BLACK: "#00293B",
  LINE: "rgba(0,41,59,0.2)",
  DARK_LINE: "#343740",
  FONT: "rgba(0,41,59,0.7)",
  RED: "#E7475A",
  BLUE: "#0098D1",
  LIGHT_BLUE: "#9FD8EE",
  DARK_BLUE: "#0B3267",
  GREY: "#9EA0A3",
  MEDIUM_GREY: "#E5E5E5",
  MEDIUM_GREY_LINES: "#ddd",
  LIGHT_GREY_BG: "#F6F6F6",
  ORANGE: "#F5811F",
  METRIC_GRADIENT: [
    [0, "#0098D1"],
    [0.9, "#0B3267"],
    [0.99, "#E7475A"],
    [1, "#F5811F"],
  ],
  METRIC_GRADIENT_MINIMIZED: [
    [0, "#F5811F"],
    [0.01, "#E7475A"],
    [0.1, "#0B3267"],
    [1, "#0098D1"],
  ],
  CHECKPOINTS_PALETTE: [
    "#332288",
    "#117733",
    "#44AA99",
    "#88CCEE",
    "#CC6677",
    "#AA4499",
    "#882255",
  ],
};
