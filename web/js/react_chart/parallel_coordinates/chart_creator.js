/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ui from "../../experiment/ui";
import {AxisTypes, CHART_COLORS} from "../../chart/constants";
import {NULL_METRIC_NAME} from "../../constants";
import {ParameterTransformations} from "../../experiment/constants";
import {axisValueGetter} from "../../chart/values";
import {idKey, isDefinedAndNotNull} from "../../utils";
import {parallelCoordinatesTemplates} from "./template";

const getParameter = function (experiment, parameterKey) {
  return _.findWhere(experiment.parameters, {name: parameterKey});
};

const axisStringOptionsGetters = {
  [AxisTypes.TASK]: (_unused, experiment) =>
    _.pluck(_.sortBy(experiment.tasks, "cost"), "name"),
  [AxisTypes.PARAMETER]: (axis, experiment) => {
    const parameter = getParameter(experiment, axis.key);
    return _.sortBy(_.pluck(parameter.categorical_values, "name"));
  },
  [AxisTypes.METADATA]: (axis, _unused, observations) => {
    const getter = axisValueGetter(axis);
    return _.chain(observations).map(getter).unique().sortBy().value();
  },
  [AxisTypes.CONDITIONAL]: (axis, experiment) =>
    _.findWhere(experiment.conditionals, {name: axis.key}).values,
};

const isAxisNumericGetters = {
  [AxisTypes.OPTIMIZED_METRIC]: () => true,
  [AxisTypes.CONSTRAINED_METRIC]: () => true,
  [AxisTypes.STORED_METRIC]: () => true,
  [AxisTypes.TASK]: () => false,
  [AxisTypes.CONDITIONAL]: () => false,
  [AxisTypes.METADATA]: (axis, _unused, observations) => {
    const getter = axisValueGetter(axis);
    return _.chain(observations).map(getter).every(_.isNumber).value();
  },
  [AxisTypes.PARAMETER]: (axis, experiment) => {
    const parameter = getParameter(experiment, axis.key);
    return !parameter.categorical_values;
  },
};

const numericAxisFixedRangeGetters = {
  [AxisTypes.OPTIMIZED_METRIC]: () => false,
  [AxisTypes.CONSTRAINED_METRIC]: () => false,
  [AxisTypes.STORED_METRIC]: () => false,
  [AxisTypes.METADATA]: () => false,
  [AxisTypes.PARAMETER]: (axis, experiment, observations) => {
    const parameter = getParameter(experiment, axis.key);
    const parameterValues = _.chain(observations)
      .pluck("assignments")
      .pluck(axis.key)
      .filter(isDefinedAndNotNull)
      .value();
    const getBound = (value, agg) =>
      agg(_.flatten([parameterValues, [value]], true));
    return [
      getBound(parameter.bounds.min, _.min),
      getBound(parameter.bounds.max, _.max),
    ];
  },
};

const createMetricConstraintRange = function (
  dimension,
  axis,
  experiment,
  observations,
  bestAssignments,
  isParetoOptimizedExperiment,
) {
  const METRIC_DEFAULT_SELECT_PERCENT = 10;
  const metric = ui.findMetric(experiment, axis.key);
  const [min, max] = dimension.range;
  if (axis.type === AxisTypes.CONSTRAINED_METRIC) {
    return ui.metricObjectiveOption(metric, {
      minimize: [min, ui.getThreshold(experiment, axis.key)],
      maximize: [ui.getThreshold(experiment, axis.key), max],
    });
  }
  if (isParetoOptimizedExperiment) {
    const getter = axisValueGetter(axis);
    const observationValues = _.map(observations, getter);
    const bestValues = _.map(bestAssignments, getter);
    return ui.metricObjectiveOption(metric, {
      minimize: [_.min(observationValues), _.max(bestValues)],
      maximize: [_.min(bestValues), _.max(observationValues)],
    });
  } else {
    const rangeSize = ((max - min) * METRIC_DEFAULT_SELECT_PERCENT) / 100;
    return ui.metricObjectiveOption(metric, {
      minimize: [min, min + rangeSize],
      maximize: [max - rangeSize, max],
    });
  }
};

const adjustLogScaleDimension = function (
  dimension,
  n = 5,
  fractionDigits = 1,
) {
  dimension.type = "log";
  const originRange = dimension.range;
  dimension.values = _.map(dimension.values, (v) => Math.log10(v));
  dimension.range = _.map(dimension.range, (v) => Math.log10(v));
  dimension.constraintrange = _.map(dimension.constraintrange, (v) =>
    Math.log10(v),
  );

  const [min, max] = dimension.range;
  const diff = (max - min) / n;
  dimension.tickvals = [...dimension.range];
  dimension.ticktext = [...originRange];
  for (let i = 1; i < n; i += 1) {
    const v = min + i * diff;
    dimension.tickvals.push(v);
    dimension.ticktext.push(10 ** v);
  }
  dimension.ticktext = _.map(dimension.ticktext, (x) =>
    x.toExponential(fractionDigits),
  );
};

const createNumericDimension = function (
  axis,
  experiment,
  observations,
  bestAssignments,
  isParetoOptimizedExperiment,
) {
  const dimension = {
    label: axis.label,
    range: [],
    constraintrange: [],
    // This is hard to get something that looks good and makes sense for all value types...
    tickformat: "g",
    values: [],
  };

  const getter = axisValueGetter(axis);
  dimension.values = _.chain(observations).sortBy(idKey).map(getter).value();

  const fixedRange = numericAxisFixedRangeGetters[axis.type](
    axis,
    experiment,
    observations,
  );
  if (fixedRange) {
    dimension.range = fixedRange;
  } else {
    dimension.range = [_.min(dimension.values), _.max(dimension.values)];
  }

  if (
    axis.type === AxisTypes.OPTIMIZED_METRIC ||
    axis.type === AxisTypes.CONSTRAINED_METRIC
  ) {
    dimension.constraintrange = createMetricConstraintRange(
      dimension,
      axis,
      experiment,
      observations,
      bestAssignments,
      isParetoOptimizedExperiment,
    );
  } else {
    dimension.constraintrange = dimension.range;
  }

  const parameter = getParameter(experiment, axis.key);
  if (parameter && parameter.transformation === ParameterTransformations.LOG) {
    adjustLogScaleDimension(dimension);
  }

  return dimension;
};

const createStringDimension = function (axis, experiment, observations) {
  const options = axisStringOptionsGetters[axis.type](
    axis,
    experiment,
    observations,
  );

  const dimension = {
    label: axis.label,
    ticktext: options,
    tickvals: _.range(options.length),
    range: [0, options.length - 1],
    constraintrange: [0, options.length - 1],
    values: [],
  };

  const getter = axisValueGetter(axis);
  dimension.values = _.chain(observations)
    .sortBy(idKey)
    .map((observation) => {
      const stringValue = getter(observation);
      return dimension.tickvals[dimension.ticktext.indexOf(stringValue)];
    })
    .value();

  return dimension;
};

const createPlotlyDimensions = function (
  selectedAxes,
  experiment,
  observations,
  bestAssignments,
  isParetoOptimizedExperiment,
) {
  return _.map(selectedAxes, (axis) => {
    const axisIsNumeric = isAxisNumericGetters[axis.type](
      axis,
      experiment,
      observations,
    );
    if (axisIsNumeric) {
      return createNumericDimension(
        axis,
        experiment,
        observations,
        bestAssignments,
        isParetoOptimizedExperiment,
      );
    } else {
      return createStringDimension(axis, experiment, observations);
    }
  });
};

const createPlotlyLine = function (
  experiment,
  observations,
  bestAssignments,
  isParetoOptimizedExperiment,
) {
  if (ui.isSearchExperiment(experiment)) {
    return parallelCoordinatesTemplates.basicline;
  }

  const sortedObs = _.sortBy(observations, idKey);
  if (isParetoOptimizedExperiment) {
    const bestAssignmentIds = _.pluck(bestAssignments, "id");
    const color = _.map(sortedObs, (o) =>
      _.contains(bestAssignmentIds, o.id) ? 1 : 0,
    );
    return _.extend({}, parallelCoordinatesTemplates.fragments.paretoline, {
      color,
    });
  } else {
    const line = _.extend(
      {},
      parallelCoordinatesTemplates.fragments.scaleline,
      {
        color: _.map(
          sortedObs,
          (o) => ui.optimizedValues(experiment, o.values)[0],
        ),
      },
    );
    const metric = ui.optimizedMetrics(experiment)[0];
    line.colorbar.title = metric.name || NULL_METRIC_NAME;
    line.colorscale = ui.metricObjectiveOption(metric, {
      minimize: CHART_COLORS.METRIC_GRADIENT_MINIMIZED,
      maximize: CHART_COLORS.METRIC_GRADIENT,
    });
    return line;
  }
};

export const createPlotlyParallelCoordinatesChartJSON = function (
  selectedAxes,
  experiment,
  successfulObservationsLessBestAssignments,
  bestAssignments,
  paretoOnly,
) {
  const observations = bestAssignments.concat(
    paretoOnly ? [] : successfulObservationsLessBestAssignments,
  );
  const getters = _.map(selectedAxes, axisValueGetter);
  const satisfiedObservations = _.filter(observations, (o) =>
    _.chain(getters)
      .map((getter) => getter(o))
      .every(isDefinedAndNotNull)
      .value(),
  );
  const isParetoOptimizedExperiment =
    ui.isParetoOptimizedExperiment(experiment);

  const plotlyDimensions = createPlotlyDimensions(
    selectedAxes,
    experiment,
    satisfiedObservations,
    bestAssignments,
    isParetoOptimizedExperiment,
  );
  const plotlyLine = createPlotlyLine(
    experiment,
    satisfiedObservations,
    bestAssignments,
    isParetoOptimizedExperiment,
  );

  const chart = _.extend({}, parallelCoordinatesTemplates.base_template);
  chart.data[0].dimensions = plotlyDimensions;
  chart.data[0].line = plotlyLine;

  return chart;
};
