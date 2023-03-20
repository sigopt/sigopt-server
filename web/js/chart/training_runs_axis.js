/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {NULL_METRIC_NAME} from "../constants";
import {getChartRange} from "./range";

class TrainingRunsAxis {
  constructor(maxCheckpoints, data, options) {
    this.maxCheckpoints = maxCheckpoints;
    this.data = data;
    this.options = options;
  }

  layout = {};

  // implemented by base classes
  // getCheckpointValue(trainingRun, checkpoint, ordinal) => number/string
  getCheckpointValue = () => {
    throw new Error("getCheckpointValue not implemented");
  };
}

class TrainingRunsCheckpointAxis extends TrainingRunsAxis {
  layout = {
    autoRange: false,
    range: [0, this.maxCheckpoints + 1],
    title: "Checkpoint Number",
  };

  getCheckpointValue = (trainingRun, checkpoint, ordinal) => ordinal;
}

class TrainingRunsTimeAxis extends TrainingRunsAxis {
  maxTimeDelta = _.chain(this.data)
    .map(({checkpoints, trainingRun}) => {
      const startTime = trainingRun.created;
      const times = [trainingRun.updated].concat(
        _.pluck(checkpoints, "created"),
      );
      const endTime = _.max(times);
      return endTime - startTime;
    })
    .max()
    .value();

  get _scale() {
    if (this.maxTimeDelta < 90) {
      return {
        label: "Seconds",
        factor: 1,
      };
    }
    const minutesDelta = this.maxTimeDelta / 60;
    if (minutesDelta < 90) {
      return {
        label: "Minutes",
        factor: 1 / 60,
      };
    }
    return {
      label: "Hours",
      factor: 1 / 3600,
    };
  }

  scale = this._scale;

  layout = {
    autorange: false,
    title: this.scale.label,
    range: getChartRange(0, this.maxTimeDelta * this.scale.factor),
  };

  getCheckpointValue = (trainingRun, checkpoint) =>
    (checkpoint.created - trainingRun.created) * this.scale.factor;
}

class TrainingRunsMetadataAxis extends TrainingRunsAxis {
  metadataKey = this.options.metadataKey;

  layout = {title: this.metadataKey};

  getCheckpointValue = (trainingRun, checkpoint) =>
    (checkpoint.metadata || {})[this.metadataKey];
}

class TrainingRunsMetricAxis extends TrainingRunsAxis {
  metricName = this.options.metricName;

  layout = {title: this.metricName || NULL_METRIC_NAME};

  getCheckpointValue = (trainingRun, checkpoint) =>
    _.chain(checkpoint.values)
      .filter(({name}) => name === this.metricName)
      .pluck("value")
      .first()
      .value();
}

export const [CHECKPOINT_AXIS, TIME_AXIS] = ["checkpoint", "time"];

export const TrainingRunsAxisOptions = {
  [CHECKPOINT_AXIS]: {
    Cls: TrainingRunsCheckpointAxis,
    key: CHECKPOINT_AXIS,
    label: "Checkpoint",
  },
  [TIME_AXIS]: {
    Cls: TrainingRunsTimeAxis,
    key: TIME_AXIS,
    label: "Time",
  },
};

export const getMetadataAxisOption = (metadataKey) => ({
  Cls: TrainingRunsMetadataAxis,
  key: `metadata:${metadataKey}`,
  label: metadataKey,
  options: {metadataKey},
});

export const metricAxisOption = (name) => ({
  Cls: TrainingRunsMetricAxis,
  key: `metric:${name}`,
  label: name,
  options: {metricName: name},
});

export const getMetricAxisOptions = (metrics) =>
  _.map(metrics, ({name}) => metricAxisOption(name));

export const createAxis = (axisOption, maxCheckpoints, data) =>
  new axisOption.Cls(maxCheckpoints, data, axisOption.options);
