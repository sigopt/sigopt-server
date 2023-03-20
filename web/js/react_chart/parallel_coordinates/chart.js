/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Chart from "../../chart/chart";
import {createPlotlyParallelCoordinatesChartJSON} from "./chart_creator";

export default class ParallelCoordinatesChart extends Chart {
  getChartArgs(args, selectedAxes, paretoOnly) {
    return createPlotlyParallelCoordinatesChartJSON(
      selectedAxes,
      args.experiment,
      args.notFailuresLessBestAssignments,
      args.bestAssignments,
      paretoOnly,
    );
  }
}
