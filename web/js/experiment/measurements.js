/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./metrics.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import schemas from "../react/schemas";
import ui from "./ui";
import {MeasurementsTableBody, TableCard, TableHeader} from "./tables";
import {MetricStrategy} from "./constants";

const Failure = ({editing, failed, onChange}) => {
  if (!editing && !failed) {
    return null;
  }
  let component = (
    <div className="field-value">
      <h2>Failed</h2>
    </div>
  );
  if (editing) {
    component = (
      <label className={classNames("failure-label", {failed: failed})}>
        <input
          type="checkbox"
          checked={Boolean(failed)}
          className="checkbox failure-input"
          name="failed"
          onChange={onChange}
        />
        <span>Failed</span>
      </label>
    );
  }
  return <div className="metric-failure">{component}</div>;
};

const MeasurementsTable = ({
  editing,
  experiment,
  failed,
  header,
  measurements,
  onChange,
  onClick,
  scrollable,
  submitting,
}) => (
  <TableCard
    onClick={onClick}
    scrollable={scrollable}
    measurements={true}
    copyObject={measurements}
  >
    <TableHeader className="main-header" nameHeader={header || "Metrics"} />
    <TableHeader
      nameHeader="Metric Name"
      valueHeader="Value"
      stddevHeader="Standard Deviation"
    />
    <MeasurementsTableBody
      editing={editing}
      experiment={experiment}
      failed={failed}
      measurements={measurements}
      onChange={onChange}
      submitting={submitting}
    />
  </TableCard>
);

export class MeasurementsView extends React.Component {
  static propTypes = {
    editing: PropTypes.bool,
    experiment: schemas.Experiment.isRequired,
    failed: PropTypes.bool,
    measurements: PropTypes.arrayOf(PropTypes.object.isRequired),
    onChange: PropTypes.func,
    submitting: PropTypes.bool,
  };

  getMeasurements = () => {
    if (_.isEmpty(this.props.measurements)) {
      return ui.getInitialValues(this.props.experiment);
    }
    return this.props.measurements;
  };

  onFailureChange = () =>
    this.props.onChange(this.getMeasurements(), !this.props.failed);

  onMeasurementChange = (name, attr, rawValue) => {
    this.props.onChange(
      _.map(this.getMeasurements(), (measurement) =>
        measurement.name === name
          ? _.extend({}, measurement, {[attr]: rawValue})
          : measurement,
      ),
      this.props.failed,
    );
  };

  render() {
    const measurementsByStrategy = ui.groupMeasurementsByStrategy(
      this.props.experiment,
      this.getMeasurements(),
    );
    const optimizedMeasurements =
      measurementsByStrategy[MetricStrategy.OPTIMIZE];
    const constrainedMeasurements =
      measurementsByStrategy[MetricStrategy.CONSTRAINT];
    const storedMeasurements = measurementsByStrategy[MetricStrategy.STORE];
    return (
      <div className="metrics-view">
        <Failure
          editing={this.props.editing}
          failed={this.props.failed}
          onChange={this.onFailureChange}
        />
        <div className="display-row">
          <MeasurementsTable
            editing={this.props.editing}
            experiment={this.props.experiment}
            failed={this.props.failed}
            header="Optimized Metrics"
            measurements={optimizedMeasurements}
            onChange={this.onMeasurementChange}
            submitting={this.props.submitting}
          />
        </div>
        {_.size(constrainedMeasurements) > 0 && (
          <div className="display-row">
            <MeasurementsTable
              editing={this.props.editing}
              experiment={this.props.experiment}
              failed={this.props.failed}
              header="Constrained Metrics"
              measurements={constrainedMeasurements}
              onChange={this.onMeasurementChange}
              submitting={this.props.submitting}
            />
          </div>
        )}
        {_.size(storedMeasurements) > 0 && (
          <div className="display-row">
            <MeasurementsTable
              editing={this.props.editing}
              experiment={this.props.experiment}
              failed={this.props.failed}
              header="Stored Metrics"
              measurements={storedMeasurements}
              onChange={this.onMeasurementChange}
              submitting={this.props.submitting}
            />
          </div>
        )}
      </div>
    );
  }
}
