/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import MpmHistogram from "../chart/mpm_histogram";
import ReactChart from "../react_chart/react_chart";
import {naturalStringCompare} from "../utils";

const groupMetrics = (metrics, minGroupSize = 3) => {
  const groups = _.groupBy(metrics, (name) =>
    name.slice(0, Math.max(0, name.indexOf("-"))),
  );
  const [defaultGroups, rest] = _.partition(
    _.pairs(groups),
    ([k, v]) => !k || v.length < minGroupSize,
  );
  const defaultGroup = _.reduceRight(
    defaultGroups,
    (a, [, v]) => a.concat(v),
    [],
  );
  const allGroups = rest;
  if (defaultGroup.length) {
    allGroups.push(["", defaultGroup]);
  }
  return _.map(
    _.sortBy(allGroups, ([k]) => k),
    ([, v]) => v,
  );
};

const TrainingRunHistogramGroup = ({
  focusedRuns,
  metrics,
  runs,
  traceLabels,
  showThisRun,
}) => (
  <div className="run-histograms">
    {_.map(metrics.sort(naturalStringCompare), (metricName) => (
      <div className="run-histogram" key={metricName}>
        <ReactChart
          args={{
            data: [
              {
                metricName,
                runs,
                focusedRuns,
              },
            ],
            layout: {
              autosize: false,
              height: 155,
              width: 400,
              margin: {
                l: 30,
                r: 30,
                t: 35,
                b: 45,
                pad: 0,
              },
              title: {
                text: metricName,
                pad: {
                  t: 10,
                  b: 10,
                },
                x: 0.5,
                xanchor: "center",
                xref: "paper",
                y: 1,
                yanchor: "bottom",
                yref: "paper",
              },
            },
            showThisRun,
            traceLabels,
          }}
          cls={MpmHistogram}
        />
      </div>
    ))}
  </div>
);

export default ({focusedRuns, metrics, runs, traceLabels, showThisRun}) => {
  const groups = groupMetrics(metrics);
  return _.map(groups, (group, index) => (
    <>
      <TrainingRunHistogramGroup
        focusedRuns={focusedRuns}
        metrics={group}
        runs={runs}
        traceLabels={traceLabels}
        showThisRun={showThisRun}
      />
      {index !== groups.length - 1 && <hr className="solid" />}
    </>
  ));
};
