/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import ui from "./ui";
import {MetricStrategy} from "./constants";
import {MetricsTableBody, TableCard, TableHeader} from "./tables";

const BestAssignmentsTable = ({bestObservation, experiment, onClick}) => {
  const measurementsByStrategy = ui.groupMeasurementsByStrategy(
    experiment,
    bestObservation.values,
  );
  const optimizedMeasurements = measurementsByStrategy[MetricStrategy.OPTIMIZE];
  return (
    <TableCard onClick={onClick} copyObject={bestObservation}>
      <TableHeader nameHeader="Metric" valueHeader="Value" />
      <MetricsTableBody values={optimizedMeasurements} />
    </TableCard>
  );
};

export default BestAssignmentsTable;
