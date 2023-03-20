/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ImprovementChart from "../../chart/improvement_chart";
import ReactChart from "../react_chart";
import layout from "../layout";
import makeBestSeenTrace from "../../chart/best_seen_trace";
import schemas from "../../react/schemas";
import sort_observations from "../../experiment/sort_observations";
import ui from "../../experiment/ui";
import {NULL_METRIC_NAME} from "../../constants";
import {isDefinedAndNotNull} from "../../utils";
import {metricValueGetter} from "../../chart/values";

class ExperimentImprovementChart extends React.Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    metric: PropTypes.object,
    observations: PropTypes.arrayOf(
      schemas.observationRequiresFields(["values"]),
    ).isRequired,
    onClickHandler: PropTypes.func,
  };

  getBestSeenTraces(experiment, observations, metric) {
    if (!(isDefinedAndNotNull(observations) && observations.length > 0)) {
      return [];
    }
    // NOTE: at this time, this is only used for single-metric experiments
    const getValue = (o) => metricValueGetter(o, metric.name);
    const rejectFailed = _.property("failed");
    const rejectThreshold = (o) =>
      !ui.observationSatisfiesThresholds(experiment, o);
    const rejectPartialCost = ({task}) => task && task.cost !== 1;
    const rejectFullCost = ({task}) => (task ? task.cost === 1 : true);
    const rejectAny = (rejections) => (o) => _.any(rejections, (r) => r(o));
    const traces = [
      {
        name: "Full Cost",
        reject: rejectAny([rejectFailed, rejectThreshold, rejectPartialCost]),
      },
    ].concat(
      experiment.tasks
        ? [
            {
              name: experiment.tasks
                ? "Partial Cost"
                : metric.name || NULL_METRIC_NAME,
              reject: rejectAny([
                rejectFailed,
                rejectThreshold,
                rejectFullCost,
              ]),
            },
          ]
        : [],
    );
    const sorted_observations = sort_observations(observations);
    return _.map(traces, ({name, reject}) => ({
      name,
      points: makeBestSeenTrace(sorted_observations, {
        aggregate: ui.metricObjectiveOption(metric, {
          minimize: _.min,
          maximize: _.max,
        }),
        getValue,
        reject,
      }),
    }));
  }

  render() {
    const traces = this.getBestSeenTraces(
      this.props.experiment,
      this.props.observations,
      this.props.metric,
    );
    return (
      <div>
        <ReactChart
          args={{
            data: [this.props.experiment, traces],
            layout: layout,
            onClickHandler: this.props.onClickHandler,
          }}
          cls={ImprovementChart}
        />
      </div>
    );
  }
}

export default ExperimentImprovementChart;
