/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Component from "../../react/component";
import XmarkGlyph from "../../component/glyph/xmark";
import schemas from "../../react/schemas";
import ui from "../ui";
import {
  VerticalTableBodyWrapper,
  VerticalTableField,
  VerticalTableWrapper,
} from "../vertical_table";
import {isDefinedAndNotNull, isUndefinedOrNull} from "../../utils";

const ThresholdInputWrapper = ({children}) => (
  <div className="threshold-input">{children}</div>
);

class ThresholdInput extends React.Component {
  _applyChange = (threshold) => {
    const updatedMetrics = _.map(this.props.metrics, (metric) =>
      metric.name === this.props.metricName
        ? _.extend({}, metric, {threshold})
        : metric,
    );
    this.props.onMetricsEditChange(updatedMetrics);
  };

  onCreate = () => this._applyChange("");

  onChange = (event) => this._applyChange(event.target.value);

  onRemove = () => this._applyChange(null);

  render() {
    const metric = _.findWhere(this.props.metrics, {
      name: this.props.metricName,
    });
    if (isDefinedAndNotNull(metric.threshold)) {
      return (
        <ThresholdInputWrapper>
          <input
            required={true}
            type="text"
            className="form-control"
            placeholder="Threshold"
            onChange={this.onChange}
            value={metric.threshold}
          />
          {ui.isMetricOptimized(metric) && (
            <a
              tabIndex="-1"
              onClick={this.onRemove}
              className="btn btn-xs btn-remove remove-threshold-button"
            >
              <XmarkGlyph />
            </a>
          )}
        </ThresholdInputWrapper>
      );
    }
    return (
      <ThresholdInputWrapper>
        <a
          className="btn btn-sm create-threshold-button"
          onClick={this.onCreate}
        >
          Create threshold
        </a>
      </ThresholdInputWrapper>
    );
  }
}

export class MetricsExtendedTable extends Component {
  static propTypes = {
    editing: PropTypes.bool.isRequired,
    experiment: schemas.Experiment.isRequired,
    onMetricsEditChange: PropTypes.func.isRequired,
  };

  render() {
    return (
      <VerticalTableWrapper className="metrics-table">
        {_.map(this.props.experiment.metrics, (metric) => (
          <VerticalTableBodyWrapper key={metric.name || "metric"}>
            <VerticalTableField
              dataKey="name"
              label="Name"
              content={metric.name}
            />
            <VerticalTableField
              dataKey="objective"
              label="Objective"
              content={metric.objective}
            />
            {ui.thresholdAllowedForMetric(this.props.experiment, metric) && (
              <VerticalTableField
                dataKey="threshold"
                label="Threshold"
                content={
                  this.props.editing ? (
                    <ThresholdInput
                      metrics={this.props.experiment.metrics}
                      metricName={metric.name}
                      onMetricsEditChange={this.props.onMetricsEditChange}
                    />
                  ) : (
                    <span
                      className={
                        isUndefinedOrNull(metric.threshold)
                          ? "no-threshold"
                          : null
                      }
                    >
                      {metric.threshold}
                    </span>
                  )
                }
              />
            )}
            <VerticalTableField
              dataKey="strategy"
              label="Strategy"
              content={metric.strategy}
            />
          </VerticalTableBodyWrapper>
        ))}
      </VerticalTableWrapper>
    );
  }
}
