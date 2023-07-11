/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import natCompare from "natural-compare-lite";

import byNaturalSortName from "./sort_params";
import {
  InteractionStates,
  MetricStrategy,
  ParameterTransformations,
  ParameterTypes,
} from "./constants";
import {
  ignoreBlanks,
  isDefinedAndNotNull,
  isUndefinedOrNull,
  maybeAsNumber,
  renderNumber,
} from "../utils";

const ui = {
  isExperimentSingleBest: function (experiment) {
    return (
      !ui.isParetoOptimizedExperiment(experiment) &&
      (experiment.num_solutions || 1) === 1
    );
  },

  parameterEnabled: function (experiment, assignments, parameterName) {
    const parameter = _.find(
      experiment.parameters,
      (p) => p.name === parameterName,
    );
    return (
      _.isEmpty(parameter.conditions) ||
      _.chain(parameter.conditions)
        .map((acceptedConditionalValues, conditionalName) => {
          const condition = _.find(
            experiment.conditionals,
            (c) => c.name === conditionalName,
          );
          const conditionAssignment = assignments[conditionalName];
          if (_.contains(condition.values, conditionAssignment)) {
            return _.contains(acceptedConditionalValues, conditionAssignment);
          }
          return true;
        })
        .every()
        .value()
    );
  },

  // Avoid returning null/undefined here. The two most common cases are
  //    1) This is in a React <input value={ui.renderParamValue(...)}/>,
  //       in which case `null` has unexpected behaviour
  //    2) The `null` is indicative of a bug - in which case it's probably
  //       better to just render '' instead of actually 'null'
  renderInputValue: (value) =>
    isDefinedAndNotNull(value) ? value.toString() : "",

  validNumberInput: (value) =>
    value.match(/^-?[0-9]*\.?[0-9]*(?:[eE]-?[0-9]*)?$/u),

  validPositiveNumberInput: (value) =>
    value.match(/^[0-9]*\.?[0-9]*(?:[eE]-?[0-9]*)?$/u),

  validIntegerInput: (value) => value.match(/^-?[0-9]*(?:[eE][0-9]*)?$/u),

  renderParamValue: function (parameter, paramValue, round) {
    if (typeof paramValue === "string") {
      return paramValue;
    } else if (
      isDefinedAndNotNull(parameter) &&
      isDefinedAndNotNull(paramValue)
    ) {
      if (parameter.type === ParameterTypes.DOUBLE) {
        return renderNumber(paramValue, round);
      } else if (parameter.type === ParameterTypes.INTEGER) {
        return paramValue.toFixed(0);
      }
    }
    return this.renderInputValue(paramValue);
  },

  getInitialValues: function (experiment) {
    return _.map(experiment.metrics, ({name}) => ({
      name,
      value: null,
      value_stddev: null,
    }));
  },

  getInitialTask: function (experiment) {
    return experiment.tasks ? _.last(_.sortBy(experiment.tasks, "cost")) : null;
  },

  getInitialAssignments: function (experiment) {
    const conditionalAssignments = _.map(experiment.conditionals, (c) => [
      c.name,
      c.values[0],
    ]);
    const parameterAssignments = _.map(experiment.parameters, (p) => [
      p.name,
      _.isEmpty(p.categorical_values) ? null : p.categorical_values[0].name,
    ]);

    return _.object(conditionalAssignments.concat(parameterAssignments));
  },

  renderAssignments: function (experiment, assignments) {
    if (!experiment) {
      return {};
    }
    const conditionalAssignments = _.map(experiment.conditionals, (c) => [
      c.name,
      assignments[c.name],
    ]);
    let parameterAssignments = _.chain(experiment.parameters);
    if (!_.isEmpty(experiment.conditionals)) {
      parameterAssignments = parameterAssignments.filter((p) =>
        _.has(assignments, p.name),
      );
    }
    parameterAssignments = parameterAssignments
      .map((p) => [p.name, ui.renderParamValue(p, assignments[p.name])])
      .value();
    return _.object(conditionalAssignments.concat(parameterAssignments));
  },

  sanitizeAssignments: function (experiment, assignments) {
    const sanitizeNumber = _.compose(ignoreBlanks, maybeAsNumber);

    const conditionalAssignments = _.map(experiment.conditionals, (c) => [
      c.name,
      assignments[c.name],
    ]);
    const parameterAssignments = _.chain(experiment.parameters)
      .filter((p) => ui.parameterEnabled(experiment, assignments, p.name))
      .map((p) => {
        const assignment = assignments[p.name];
        return [
          p.name,
          p.type === ParameterTypes.CATEGORICAL
            ? assignment
            : sanitizeNumber(assignment),
        ];
      })
      .filter((e) => isDefinedAndNotNull(e[1]))
      .value();

    return _.object(conditionalAssignments.concat(parameterAssignments));
  },

  sanitizeValues: function (values) {
    return _.map(values, (v) => ({
      name: isDefinedAndNotNull(v.name) ? v.name.toString() : null,
      value: maybeAsNumber(v.value),
      value_stddev:
        v.value_stddev === "" ? null : maybeAsNumber(v.value_stddev),
    }));
  },

  sanitizeObservation: function (experiment, observation, initialObservation) {
    const sanitizedObservation = _.pick(
      observation,
      "assignments",
      "failed",
      "values",
    );
    const sanitizedAssignments =
      sanitizedObservation.assignments &&
      ui.sanitizeAssignments(experiment, sanitizedObservation.assignments);
    const suggestionId =
      observation.suggestion || (initialObservation || {}).suggestion;
    if (
      suggestionId &&
      (!sanitizedAssignments ||
        (initialObservation &&
          _.isEqual(sanitizedAssignments, initialObservation.assignments)))
    ) {
      sanitizedObservation.assignments = null;
      sanitizedObservation.suggestion = suggestionId;
    } else {
      sanitizedObservation.assignments = sanitizedAssignments;
      sanitizedObservation.suggestion = null;
    }
    if (sanitizedObservation.failed) {
      sanitizedObservation.values = null;
    } else {
      sanitizedObservation.values = ui.sanitizeValues(
        sanitizedObservation.values,
      );
    }
    return sanitizedObservation;
  },

  isEmptyInputValue: (value) => !isDefinedAndNotNull(value) || value === "",

  validateValuesInput: function (experiment, values, failed, onAlert) {
    const makeAlert = onAlert || _.noop;
    if (isDefinedAndNotNull(failed) && typeof failed !== "boolean") {
      makeAlert("The value for failed must be true or false");
      return false;
    }
    return _.every(experiment.metrics, (m) => {
      const {value, value_stddev} =
        _.find(values, (v) => v.name === m.name) || {};
      const metricName = m.name ? `'${m.name}' ` : "";
      if (failed) {
        if (isDefinedAndNotNull(value)) {
          makeAlert(`The metric ${metricName}cannot have a value if it failed`);
          return false;
        }
        if (isDefinedAndNotNull(value_stddev)) {
          makeAlert(
            `The metric ${metricName}cannot have a standard deviation if it failed`,
          );
          return false;
        }
        return true;
      }
      if (typeof value !== "number") {
        makeAlert(
          `The value for the metric ${metricName}must be a valid number`,
        );
        return false;
      }
      if (
        isDefinedAndNotNull(value_stddev) &&
        typeof value_stddev !== "number"
      ) {
        makeAlert(
          `The standard deviation for the metric ${metricName}is not a valid number`,
        );
        return false;
      }
      return true;
    });
  },

  validateAssignmentsInput: function (experiment, assignments, onAlert) {
    const makeAlert = onAlert || _.noop;
    const validateParameter = (parameter) => {
      if (ui.parameterEnabled(experiment, assignments, parameter.name)) {
        if (ui.isEmptyInputValue(assignments[parameter.name])) {
          makeAlert(`The value for parameter '${parameter.name}' is required`);
          return false;
        }
        return true;
      } else {
        if (!ui.isEmptyInputValue(assignments[parameter[name]])) {
          makeAlert(
            `The parameter '${parameter.name}' does not have its conditions satisfied and should be empty`,
          );
          return false;
        }
        return true;
      }
    };
    return _.every(experiment.parameters, validateParameter);
  },

  validateObservationInput: function (experiment, observationInput, onAlert) {
    const makeAlert = onAlert || _.noop;
    if (observationInput.suggestion && observationInput.assignments) {
      makeAlert(
        "An observation cannot be reported with a suggestion and assignments",
      );
      return false;
    }
    if (!observationInput.suggestion && !observationInput.assignments) {
      makeAlert(
        "An observation must be reported with either a suggestion or assignments",
      );
      return false;
    }
    if (
      !(
        observationInput.suggestion ||
        ui.validateAssignmentsInput(
          experiment,
          observationInput.assignments,
          onAlert,
        )
      )
    ) {
      return false;
    }
    return ui.validateValuesInput(
      experiment,
      observationInput.values,
      observationInput.failed,
      onAlert,
    );
  },

  renderTaskCost: function (cost) {
    if (isDefinedAndNotNull(cost)) {
      return Number.isInteger(cost) ? cost.toFixed(1) : cost.toString();
    }
    return cost;
  },

  renderTask: function (task) {
    if (isDefinedAndNotNull(task)) {
      return `${task.name} - ${ui.renderTaskCost(task.cost)}`;
    }
    return task;
  },

  renderMetadataValue: function (value) {
    return isDefinedAndNotNull(value) ? value.toString() : value;
  },

  renderOrder: function (experiment, renderedAssignments) {
    let renderOrder = _.clone(experiment.parameters).sort(byNaturalSortName);

    if (!_.isEmpty(experiment.conditionals)) {
      renderOrder = _.filter(renderOrder, (p) =>
        isDefinedAndNotNull(renderedAssignments[p.name]),
      );
      const sortedConditionals = _.clone(experiment.conditionals).sort(
        byNaturalSortName,
      );
      renderOrder = sortedConditionals.concat(renderOrder);
    }

    return _.pluck(renderOrder, "name");
  },

  getMetadataKeys: (resources) => {
    const uniqueKeys = _.chain(resources)
      .pluck("metadata")
      .map(_.keys)
      .flatten()
      .uniq()
      .value();
    uniqueKeys.sort(natCompare);
    return uniqueKeys;
  },

  metricObjectiveOption: (metric, options) => {
    if (_.has(options, metric.objective)) {
      return options[metric.objective];
    }
    throw new Error(`Unhandled objective ${metric.objective}`);
  },

  hasThresholds: (experiment) =>
    _.find(experiment.metrics, ({threshold}) => isDefinedAndNotNull(threshold)),

  getThresholds: (experiment) =>
    _.map(experiment.metrics, (metric) => ({
      metric,
      threshold: metric.threshold,
    })),

  getThreshold: (experiment, key) => {
    const metric = ui.findMetric(experiment, key);
    if (isUndefinedOrNull(metric)) {
      return null;
    }
    return _.find(
      ui.getThresholds(experiment),
      (threshold) => threshold.metric === metric,
    ).threshold;
  },

  getThresholdMap: (experiment) =>
    _.chain(ui.getThresholds(experiment))
      .map(({metric, threshold}) => [metric.name, threshold])
      .object()
      .value(),

  valueSatisfiesThreshold: (metric, value, threshold) =>
    isUndefinedOrNull(threshold) ||
    ui.metricObjectiveOption(metric, {
      minimize: value <= threshold,
      maximize: value >= threshold,
    }),

  observationSatisfiesThresholds: (experiment, observation) => {
    if (observation.failed) {
      return false;
    }
    return _.chain(ui.getThresholds(experiment))
      .zip(observation.values)
      .filter(([{threshold}]) => isDefinedAndNotNull(threshold))
      .every(([{metric, threshold}, {value}]) =>
        ui.valueSatisfiesThreshold(metric, value, threshold),
      )
      .value();
  },

  hasObservationsThatSatisfyThresholds: (experiment, observations) =>
    _.any(observations, (obs) =>
      ui.observationSatisfiesThresholds(experiment, obs),
    ),

  thresholdsAllowedForExperiment: (experiment) =>
    ui.isParetoOptimizedExperiment(experiment) ||
    ui.hasConstrainedMetrics(experiment),

  thresholdAllowedForMetric: (experiment, metric) =>
    ui.isMetricConstrained(metric) ||
    (ui.isParetoOptimizedExperiment(experiment) &&
      ui.isMetricOptimized(metric)),

  findMetric: ({metrics}, key) => {
    if (key === null) {
      if (_.size(metrics) === 1) {
        return _.first(metrics);
      }
      return null;
    }
    if (_.isNumber(key)) {
      return metrics[key];
    }
    return _.find(metrics, ({name}) => name === key) || null;
  },

  hasMultipleMetrics: function (experiment) {
    return _.size(experiment.metrics) > 1;
  },

  optimizedMetrics: function (experiment) {
    return _.where(experiment.metrics, {strategy: MetricStrategy.OPTIMIZE});
  },

  storedMetrics: function (experiment) {
    return _.where(experiment.metrics, {strategy: MetricStrategy.STORE});
  },

  isSearchExperiment: function (experiment) {
    return ui.optimizedMetrics(experiment).length === 0;
  },

  mostImportantMetrics: function (experiment) {
    const optimizedMetrics = ui.optimizedMetrics(experiment);
    const constraintMetrics = ui.constrainedMetrics(experiment);
    const isSearchExperiment = ui.isSearchExperiment(experiment);
    return isSearchExperiment
      ? constraintMetrics.slice(0, 1)
      : optimizedMetrics;
  },

  hasStoredMetrics: function (experiment) {
    return _.size(ui.storedMetrics(experiment)) > 0;
  },

  constrainedMetrics: function (experiment) {
    return _.where(experiment.metrics, {strategy: MetricStrategy.CONSTRAINT});
  },

  hasConstrainedMetrics: function (experiment) {
    return _.size(ui.constrainedMetrics(experiment)) > 0;
  },

  isParetoOptimizedExperiment: function (experiment) {
    return _.size(ui.optimizedMetrics(experiment)) > 1;
  },

  groupMeasurementsByStrategy: function (experiment, measurements) {
    const metricNames = _.pluck(experiment.metrics, "name");
    const metricStrategies = _.pluck(experiment.metrics, "strategy");
    const nameToStrategy = _.object(metricNames, metricStrategies);
    return _.groupBy(measurements, (m) => nameToStrategy[m.name]);
  },

  optimizedValues: function (experiment, measurement) {
    const measurementsByStrategy = ui.groupMeasurementsByStrategy(
      experiment,
      measurement,
    );
    const optimizedMeasurements =
      measurementsByStrategy[MetricStrategy.OPTIMIZE];
    return _.pluck(optimizedMeasurements, "value");
  },

  isMetricOptimized: function (metric) {
    return metric.strategy === MetricStrategy.OPTIMIZE;
  },

  isMetricConstrained: function (metric) {
    return metric.strategy === MetricStrategy.CONSTRAINT;
  },

  sortMetrics: function (metrics) {
    return _.chain(metrics)
      .sortBy("name")
      .sortBy((m) => (ui.isMetricOptimized(m) ? 0 : 1))
      .value();
  },

  hasPrior: (experiment) =>
    _.find(experiment.parameters, ({prior}) => isDefinedAndNotNull(prior)),

  existingInteraction: function (interactionState) {
    return _.contains(
      [InteractionStates.MODIFY, InteractionStates.READ_ONLY],
      interactionState,
    );
  },

  inputInteraction: function (interactionState) {
    return _.contains(
      [InteractionStates.CREATE, InteractionStates.MODIFY],
      interactionState,
    );
  },

  isParameterTransformationNontrivial: function (transformation) {
    return (
      isDefinedAndNotNull(transformation) &&
      transformation !== ParameterTransformations.NONE
    );
  },

  navigateToRunForObservation: function (
    services,
    experimentId,
    observationId,
    newTab,
  ) {
    const url = `/experiment/${experimentId}/observation/${observationId}/run`;
    if (newTab) {
      services.navigator.navigateInNewTab(url);
    } else {
      services.navigator.navigateTo(url);
    }
  },

  getExperimentUrl: function (experiment, path) {
    let objectPath;
    if (ui.isAiExperiment(experiment)) {
      objectPath = "aiexperiment";
    } else {
      objectPath = "experiment";
    }
    let subPath = "";
    if (_.isObject(path)) {
      subPath = path[objectPath] || "";
    } else if (path) {
      subPath = path;
    }
    return `/${objectPath}/${experiment.id}${subPath}`;
  },

  isAiExperiment: function (experiment) {
    return experiment.object === "aiexperiment" || experiment.runs_only;
  },
};

export default ui;
