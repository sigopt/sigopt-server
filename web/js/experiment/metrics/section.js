/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import pluralize from "pluralize";

import Tooltip from "../../component/tooltip";
import {InteractionStates} from "../constants";
import {MetricsCreateTable} from "./create";
import {MetricsExtendedTable} from "./extended";
import {Section} from "../section.js";

const MetricsTooltip = function (props) {
  return (
    <Tooltip
      tooltip={
        "The value you are trying to optimize, such as revenue, " +
        "clickthrough, or model accuracy."
      }
    >
      {pluralize("Metric", props.numMetrics)}
    </Tooltip>
  );
};

export const MetricsEditSection = function (props) {
  const editing =
    props.canEditMetrics() &&
    props.interactionState === InteractionStates.MODIFY;
  return (
    <Section
      className="metric-name"
      infoClassName="experiment-parameter-info"
      heading={
        <MetricsTooltip numMetrics={props.experimentInput.metrics.length} />
      }
      sectionBody={
        <MetricsExtendedTable
          editing={editing}
          experiment={props.experimentInput}
          onMetricsEditChange={props.onMetricsEditChange}
        />
      }
    />
  );
};

export const MetricsCreateSection = function (props) {
  return (
    <div className="metric-name">
      <MetricsTooltip numMetrics={0} />
      <MetricsCreateTable
        addMetricCreate={props.addMetricCreate}
        metrics={props.metrics}
        onMetricCreateChange={props.onMetricCreateChange}
        onMetricCreateRemove={props.onMetricCreateRemove}
      />
    </div>
  );
};
