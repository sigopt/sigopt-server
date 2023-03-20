/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import Select from "react-select";

import ParallelCoordinatesChart from "./chart";
import ReactChart from "../react_chart";
import schemas from "../../react/schemas";
import ui from "../../experiment/ui";
import {AxisTypes} from "../../chart/constants";
import {NULL_METRIC_NAME} from "../../constants";
import {unifiedChartArgsProp} from "../unified_chart_args";

export default class ParallelCoordinatesWrapper extends React.Component {
  static propTypes = {
    args: unifiedChartArgsProp,
    metricImportances: PropTypes.arrayOf(schemas.MetricImportance),
  };

  constructor(props) {
    super(props);
    // Uses this as value to match against in multi-select to check whether select all was selected.
    this.SELECT_ALL_TOKEN = `SELECT_ALL_TOKEN_${Math.floor(
      Math.random() * Number.MAX_SAFE_INTEGER,
    )}`;

    const axisGroups = this.createAxisGroups(
      props.args.experiment,
      props.args.successfulObservations,
      props.args.experiment.parameters,
      props.args.metadataKeys,
    );

    const DEFAULT_NUM_AXES = 8;
    const dropdownOptions = this.createDropdownOptions(axisGroups);
    const dropdownDefaults = this.createDropdownDefaults(
      dropdownOptions,
      props.metricImportances,
      DEFAULT_NUM_AXES,
    );

    this.state = {
      dropdownOptions,
      dropdownDefaults,
      dropdownSelected: dropdownDefaults,
      paretoOnly: false,
    };
  }

  createAxisGroups(experiment, observations, parameters, metadataKeys) {
    const axisGroups = {
      "Optimized Metrics": [],
      "Stored Metrics": [],
      "Constrained Metrics": [],
      Parameters: [],
      Metadata: [],
      Tasks: [],
    };
    const createAxis = (label, key, type) => ({label, key, type});

    axisGroups["Optimized Metrics"] = _.map(
      ui.optimizedMetrics(experiment),
      (m) =>
        createAxis(
          m.name || NULL_METRIC_NAME,
          m.name,
          AxisTypes.OPTIMIZED_METRIC,
        ),
    );
    axisGroups["Constrained Metrics"] = _.map(
      ui.constrainedMetrics(experiment),
      (m) =>
        createAxis(
          m.name || NULL_METRIC_NAME,
          m.name,
          AxisTypes.CONSTRAINED_METRIC,
        ),
    );
    axisGroups["Stored Metrics"] = _.map(ui.storedMetrics(experiment), (m) =>
      createAxis(m.name || NULL_METRIC_NAME, m.name, AxisTypes.STORED_METRIC),
    );
    axisGroups.Parameters = _.map(parameters, (p) =>
      createAxis(p.name, p.name, AxisTypes.PARAMETER),
    );

    if (!_.isEmpty(metadataKeys)) {
      const metadataThatExistForAllObs = _.filter(metadataKeys, (key) =>
        _.every(observations, (o) => o.metadata && o.metadata[key]),
      );
      axisGroups.Metadata = _.map(metadataThatExistForAllObs, (key) =>
        createAxis(key, key, AxisTypes.METADATA),
      );
    }

    if (!_.isEmpty(experiment.tasks)) {
      axisGroups.Tasks = [createAxis("Tasks", "Tasks", AxisTypes.TASK)];
    }

    if (!_.isEmpty(experiment.conditionals)) {
      axisGroups.Conditionals = _.map(experiment.conditionals, (c) =>
        createAxis(c.name, c.name, AxisTypes.CONDITIONAL),
      );
    }

    return axisGroups;
  }

  createDropdownOptions(axisGroups) {
    const clonedGroupedAxes = _.clone(axisGroups);
    const nonEmptyGroupedAxes = _.pick(
      clonedGroupedAxes,
      (axes) => axes.length > 0,
    );
    const formattedGroups = _.mapObject(
      nonEmptyGroupedAxes,
      (axesGroup, key) => {
        const formattedAxes = _.map(axesGroup, (axis) =>
          _.extend({}, axis, {value: axis.label + axis.type}),
        );
        return {label: key, options: formattedAxes};
      },
    );
    const groupDisplayOrder = {
      "Optimized Metrics": 0,
      "Constrained Metrics": 1,
      "Stored Metrics": 2,
      Parameters: 3,
      Conditionals: 4,
      Tasks: 5,
      Metadata: 6,
    };
    const sortedFormattedGroups = _.sortBy(
      _.toArray(formattedGroups),
      (group) => groupDisplayOrder[group.label],
    );

    const selectAllHack = {label: "Select All", value: this.SELECT_ALL_TOKEN};
    return [selectAllHack, ...sortedFormattedGroups];
  }

  createDropdownDefaults(dropdownOptions, metricImportances, limit) {
    const constrainedMetricDropdown = _.findWhere(dropdownOptions, {
      label: "Constrained Metrics",
    });
    const storedMetricDropdown = _.findWhere(dropdownOptions, {
      label: "Stored Metrics",
    });
    const constrainedMetrics = constrainedMetricDropdown
      ? constrainedMetricDropdown.options
      : [];
    const storedMetrics = storedMetricDropdown
      ? storedMetricDropdown.options
      : [];

    const optimizedMetricsDropdown = _.findWhere(dropdownOptions, {
      label: "Optimized Metrics",
    });
    const optimizedMetrics = optimizedMetricsDropdown
      ? optimizedMetricsDropdown.options
      : [];

    const parameters = _.findWhere(dropdownOptions, {
      label: "Parameters",
    }).options;
    const parametersSortedByImportance = _.sortBy(parameters, (parameter) => {
      const firstImportance = _.first(metricImportances);
      return _.isObject(firstImportance)
        ? -firstImportance.importances[parameter.key]
        : 0;
    });

    return _.first(
      [
        ...optimizedMetrics,
        ...constrainedMetrics,
        ...storedMetrics,
        ...parametersSortedByImportance,
      ],
      limit,
    );
  }

  handleDropdownChange = (values) => {
    if (_.find(values, (element) => element.value === this.SELECT_ALL_TOKEN)) {
      const allAxes = _.map(
        this.state.dropdownOptions,
        (group) => group.options || [],
      );
      const flattenedAxes = _.flatten(allAxes);
      this.setState({dropdownSelected: flattenedAxes});
    } else {
      this.setState({dropdownSelected: values});
    }
  };

  handleParetoCheckboxChange = (e) =>
    this.setState({paretoOnly: e.target.checked});

  handleResetDefaultsClick = () =>
    this.setState((prevState) => ({
      dropdownSelected: prevState.dropdownDefaults,
    }));

  render() {
    return (
      <div>
        <ReactChart
          args={{
            data: [
              this.props.args,
              this.state.dropdownSelected,
              this.state.paretoOnly,
            ],
          }}
          cls={ParallelCoordinatesChart}
        />
        {_.isEmpty(this.state.dropdownSelected) && (
          <div className="par-coords-empty">
            Please select a combination of metrics, parameters, or metadata, or
            use the button to reset to default selection.{" "}
            <button
              type="button"
              onClick={this.handleResetDefaultsClick}
              className="btn btn-blue"
            >
              Reset
            </button>
          </div>
        )}
        <div className="controls">
          {ui.isParetoOptimizedExperiment(this.props.args.experiment) && (
            <div className="checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={this.state.paretoOnly}
                  onChange={this.handleParetoCheckboxChange}
                />{" "}
                Only Show Best Metrics
              </label>
            </div>
          )}
          <Select
            isMulti={true}
            closeMenuOnSelect={false}
            options={this.state.dropdownOptions}
            defaultValue={this.state.dropdownDefaults}
            onChange={this.handleDropdownChange}
            value={this.state.dropdownSelected}
            className="multi-select"
            classNamePrefix="multi-select"
          />
        </div>
      </div>
    );
  }
}
