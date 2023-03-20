/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import Tooltip from "../../component/tooltip";
import {MetricObjectives} from "../editor";
import {RemoveRowButton} from "../buttons/remove_button";

const MetricAddInputRow = function (props) {
  return (
    <tr>
      <td className="add-button-holder">
        <a className="btn btn-secondary add-button" onClick={props.addInput}>
          Add Metric
        </a>
      </td>
    </tr>
  );
};

const MetricObjectiveDropdown = function ({onChange, selectedObjective}) {
  return (
    <select
      className="form-control"
      onChange={onChange}
      value={selectedObjective}
    >
      {_.map(MetricObjectives, (objective) => {
        return (
          <option key={objective} value={objective}>
            {objective}
          </option>
        );
      })}
    </select>
  );
};

const MetricInputName = function (props) {
  return (
    <input
      required={true}
      onChange={props.onChange}
      className="form-control"
      type="text"
      name="name"
      placeholder="Metric Name"
      value={props.inputText || ""}
    />
  );
};
MetricInputName.propTypes = {
  inputText: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

class MetricsCreateTableRow extends React.Component {
  static propTypes = {
    metric: PropTypes.object,
    onChange: PropTypes.func.isRequired,
    onRemove: PropTypes.func.isRequired,
    rowIndex: PropTypes.number.isRequired,
  };

  updateMetricName = (e) => {
    if (e.preventDefault) {
      e.preventDefault();
      e.stopPropagation();
    }
    const newMetric = _.extend({}, this.props.metric, {name: e.target.value});
    this.props.onChange(newMetric, this.props.rowIndex);
  };

  updateMetricObjective = (e) => {
    if (e.preventDefault) {
      e.preventDefault();
      e.stopPropagation();
    }
    const newMetric = _.extend({}, this.props.metric, {
      objective: e.target.value,
    });
    this.props.onChange(newMetric, this.props.rowIndex);
  };

  render() {
    return (
      <tr>
        <td>
          <MetricInputName
            inputText={this.props.metric.name}
            onChange={(e) => this.updateMetricName(e)}
          />
        </td>
        <td>
          <MetricObjectiveDropdown
            selectedObjective={this.props.metric.objective}
            onChange={(e) => this.updateMetricObjective(e)}
          />
        </td>
        <td className="remove-row-column">
          <RemoveRowButton
            removeRow={() => {
              this.props.onRemove(this.props.rowIndex);
            }}
          />
        </td>
      </tr>
    );
  }
}

export const MetricsCreateTable = function (props) {
  return (
    <div className="table-responsive experiment-edit-table-holder metric-table">
      <table
        className={classNames({
          table: true,
          "experiment-edit-table": true,
          empty: _.isEmpty(props.metrics),
        })}
      >
        <thead>
          <tr>
            <th> Name </th>
            <th>
              <Tooltip tooltip="The objective defines the direction of improvement for the metric.">
                Objective
              </Tooltip>
            </th>
          </tr>
        </thead>
        <tbody>
          {_.map(props.metrics, (m, index) => (
            <MetricsCreateTableRow
              key={index}
              metric={m}
              onChange={props.onMetricCreateChange}
              onRemove={props.onMetricCreateRemove}
              rowIndex={index}
            />
          ))}
          <MetricAddInputRow addInput={props.addMetricCreate} />
        </tbody>
      </table>
    </div>
  );
};
