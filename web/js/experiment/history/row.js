/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import Component from "../../react/component";
import schemas from "../../react/schemas";
import ui from "../ui";
import {MeasurementValue, ValueDiv} from "../measurements_value";
import {RelativeTime} from "../../render/format_times";
import {
  isDefinedAndNotNull,
  renderNumber,
  withPreventDefault,
} from "../../utils";

const FixedCell = function (props) {
  return (
    <td
      className={classNames("fixed-td", props.className)}
      colSpan={props.colSpan}
    >
      <div className="fixed-row">
        <div className="fixed-holder">{props.children}</div>
      </div>
    </td>
  );
};

class HistoryTableRow extends Component {
  static propTypes = {
    assignments: schemas.Assignments.isRequired,
    conditionals: PropTypes.arrayOf(schemas.Conditional.isRequired),
    created: PropTypes.number,
    experiment: schemas.Experiment.isRequired,
    failed: PropTypes.bool,
    hideStdDev: PropTypes.object,
    onClick: PropTypes.func,
    parameters: PropTypes.arrayOf(schemas.Parameter.isRequired),
    resource: PropTypes.object,
    showValues: PropTypes.bool,
    taskCost: PropTypes.number,
    values: PropTypes.arrayOf(schemas.MetricEvaluation),
  };

  static defaultProps = {
    hideStdDev: {},
    onClick: _.noop,
  };

  values = () => {
    if (this.props.failed) {
      const colSpan = _.chain(this.props.experiment.metrics)
        .map((m) => (this.props.hideStdDev[m.name] ? 1 : 2))
        .reduce((mem, n) => mem + n, 0)
        .value();
      return (
        <FixedCell className="failure-cell" colSpan={colSpan}>
          <div className="failure-value">
            <div>Observation failed</div>
          </div>
        </FixedCell>
      );
    }
    return _.chain(ui.sortMetrics(this.props.experiment.metrics))
      .map((metric) => {
        const value = _.find(
          this.props.values,
          (v) => v.name === metric.name,
        ) || {
          name: metric.name,
          value: null,
          value_stddev: null,
        };
        const valueChild = (
          <MeasurementValue
            experiment={this.props.experiment}
            failed={this.props.failed}
            measurement={{
              name: value.name,
              value: value.value,
            }}
          />
        );
        const stddevChild = (
          <ValueDiv
            child={value.value_stddev && renderNumber(value.value_stddev)}
          />
        );

        return [
          <FixedCell key={`value-${value.name}`}>{valueChild}</FixedCell>,
          !this.props.hideStdDev[value.name] && (
            <FixedCell key={`value_stddev-${value.name}`}>
              {stddevChild}
            </FixedCell>
          ),
        ];
      })
      .flatten()
      .filter(isDefinedAndNotNull)
      .value();
  };

  onClick = withPreventDefault(() => this.props.onClick(this.props.resource));

  render() {
    const {
      assignments,
      conditionals,
      created,
      experiment,
      parameters,
      showValues,
      taskCost,
    } = this.props;

    const renderedAssignments = ui.renderAssignments(experiment, assignments);

    return (
      <tr
        className={classNames("history-table-row", {failed: this.props.failed})}
        onClick={this.onClick}
      >
        <FixedCell className="created">
          <RelativeTime time={created} />
        </FixedCell>
        {showValues && this.values()}
        {_.map(conditionals, (c) => (
          <FixedCell key={c.name}>
            <span className="number-value">{assignments[c.name]}</span>
          </FixedCell>
        ))}
        {taskCost && (
          <FixedCell className="task">{ui.renderTaskCost(taskCost)}</FixedCell>
        )}
        {_.map(parameters, (p) => {
          const renderedAssignment = renderedAssignments[p.name];
          return (
            <FixedCell key={p.name}>
              <ValueDiv child={renderedAssignment} />
            </FixedCell>
          );
        })}
      </tr>
    );
  }
}

export default HistoryTableRow;
