/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ReactChart from "./react_chart";
import TaskDistributionChart from "../chart/task_distribution_chart";
import schemas from "../react/schemas";
import {Dropdown, DropdownItem} from "../component/dropdown";

const yAxisOptions = ["Budget Consumed", "Observation Count"];

class TaskDistributionAxisSelector extends React.Component {
  static propTypes = {
    onSelect: PropTypes.func.isRequired,
    selected: PropTypes.string.isRequired,
  };

  render() {
    return (
      <div className="param-select-line">
        <label>y axis:</label>
        <Dropdown buttonClassName="btn btn-default" label={this.props.selected}>
          {_.map(yAxisOptions, (option) => (
            <DropdownItem key={option}>
              <a onClick={() => this.props.onSelect(option)}>{option}</a>
            </DropdownItem>
          ))}
        </Dropdown>
      </div>
    );
  }
}

export class TaskDistribution extends React.Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    observations: PropTypes.arrayOf(
      schemas.observationRequiresFields(["values"]),
    ).isRequired,
  };

  state = {
    yAxis: _.first(yAxisOptions),
  };

  render() {
    return (
      <div>
        <ReactChart
          args={{
            data: [
              this.props.experiment,
              this.props.observations,
              this.state.yAxis,
            ],
          }}
          cls={TaskDistributionChart}
        />
        <div className="param-select-holder">
          <TaskDistributionAxisSelector
            onSelect={(yAxisOption) => this.setState({yAxis: yAxisOption})}
            selected={this.state.yAxis}
          />
        </div>
      </div>
    );
  }
}
