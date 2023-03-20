/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import Tooltip from "../component/tooltip";
import ui from "./ui";
import {isDefinedAndNotNull, renderNumber} from "../utils";

export const MeasurementValue = ({experiment, failed, measurement}) => {
  let satisfied = true;
  let threshold = null;
  let metric = null;
  if (!failed && ui.thresholdsAllowedForExperiment(experiment)) {
    threshold = ui.getThreshold(experiment, measurement.name);
    metric = ui.findMetric(experiment, measurement.name);
    satisfied = ui.valueSatisfiesThreshold(
      metric,
      measurement.value,
      threshold,
    );
  }
  return satisfied ? (
    <span className="td-value" title={measurement.value}>
      <ValueDiv child={renderNumber(measurement.value)} />
    </span>
  ) : (
    <span className="failed-value" title={measurement.value}>
      <Tooltip
        tooltip={`Value does not satisfy threshold ${threshold} of ${measurement.name}`}
      >
        <ValueDiv child={renderNumber(measurement.value)} />
      </Tooltip>
    </span>
  );
};

export const ValueDiv = ({child}) => {
  if (isDefinedAndNotNull(child) && child !== "") {
    const isNumber = _.isNumber(child) || _.isFinite(child);
    return (
      <span
        className={isNumber ? "number-value" : "string-value"}
        title={child.toString()}
      >
        {renderNumber(child, true)}
      </span>
    );
  }
  return <span className="no-value" />;
};
