/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./table_card.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";
import stringify from "fast-json-stable-stringify";

import CircleArrowRightGlyph from "../component/glyph/circle-arrow-right";
import byNaturalSortName from "./sort_params";
import schemas from "../react/schemas";
import ui from "./ui";
import {ConditionalInput, ParameterInput} from "./input";
import {CopyButton} from "../component/code_block";
import {MeasurementValue} from "./measurements_value";
import {NULL_METRIC_NAME} from "../constants";
import {isDefinedAndNotNull} from "../utils";

export const TableHeader = (props) => (
  <thead className={props.className}>
    <tr>
      <th className="name" colSpan={props.valueHeader ? null : 2}>
        {props.nameHeader}
      </th>
      {props.valueHeader ? (
        <th className="value">{props.valueHeader}</th>
      ) : null}
      {props.stddevHeader ? (
        <th className="stddev">{props.stddevHeader}</th>
      ) : null}
    </tr>
  </thead>
);

const TableRow = (props) => (
  <tr className="table-row">
    {props.boldName ? (
      <th className="name" title={props.name}>
        {props.name}
      </th>
    ) : (
      <td className="name" title={props.name}>
        {props.name}
      </td>
    )}
    <td className="value" title={props.value}>
      {props.value}
    </td>
  </tr>
);

export const MetricsTableBody = ({values}) => (
  <tbody>
    {_.map(values, (v) => (
      <TableRow
        key={v.name || "metric"}
        name={v.name || NULL_METRIC_NAME}
        value={v.value}
      />
    ))}
  </tbody>
);

const MeasurementInput = ({attr, disabled, measurement, onChange}) => {
  const currentField = measurement[attr];
  const placeholder = attr === "value" ? "" : "(optional)";
  const validateInput =
    attr === "value" ? ui.validNumberInput : ui.validPositiveNumberInput;
  const validatedOnChange = (event) => {
    const rawField = event.target.value;
    const validatedField = validateInput(rawField) ? rawField : currentField;
    onChange(measurement.name, attr, validatedField);
  };

  return (
    <input
      className={classNames("form-control", attr, "data-input")}
      disabled={disabled}
      onChange={validatedOnChange}
      placeholder={placeholder}
      type="text"
      value={ui.renderInputValue(currentField)}
    />
  );
};

MeasurementInput.propTypes = {
  attr: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  measurement: PropTypes.object,
  onChange: PropTypes.func.isRequired,
};

MeasurementInput.defaultProps = {
  disabled: false,
  measurement: {},
};

const MeasurementEditRow = ({failed, measurement, onChange, submitting}) => (
  <tr className="table-row metric-view">
    <td className="name" title={measurement.name}>
      {measurement.name || NULL_METRIC_NAME}
    </td>
    {_.map(["value", "value_stddev"], (attr) => (
      <td className={`td-${attr}`} key={`td-${attr}`}>
        <MeasurementInput
          attr={attr}
          disabled={failed || submitting}
          measurement={measurement}
          onChange={onChange}
        />
      </td>
    ))}
  </tr>
);

const MeasurementTableRow = ({experiment, failed, measurement}) => (
  <tr className="table-row metric-view">
    <td className="name" title={measurement.name}>
      {measurement.name || NULL_METRIC_NAME}
    </td>
    <td>
      <MeasurementValue
        experiment={experiment}
        failed={failed}
        measurement={measurement}
      />
    </td>
    <td className="td-value_stddev" title={measurement.value_stddev}>
      {isDefinedAndNotNull(measurement.value_stddev) ? (
        <span>&plusmn;{measurement.value_stddev}</span>
      ) : (
        "-"
      )}
    </td>
  </tr>
);

export const MeasurementsTableBody = (props) => {
  const Row = props.editing ? MeasurementEditRow : MeasurementTableRow;
  return (
    <tbody>
      {_.map(props.measurements, (measurement) => (
        <Row {...props} key={measurement.name} measurement={measurement} />
      ))}
    </tbody>
  );
};

MeasurementsTableBody.defaultProps = {
  editing: false,
  failed: false,
  measurements: {},
  onChange: _.noop,
  submitting: false,
};

export const AssignmentsTableBody = ({
  assignments,
  boldName,
  editing,
  experiment,
  onChange,
  submitting,
}) => {
  const assignmentChangeHandler = (assignmentName) => (event) =>
    onChange(_.extend({}, assignments, {[assignmentName]: event.target.value}));

  const renderedAssignments = ui.renderAssignments(experiment, assignments);
  const renderOrder = ui.renderOrder(experiment, renderedAssignments);
  const makeTableRow = (name, value) => (
    <TableRow boldName={boldName} key={name} name={name} value={value} />
  );
  const conditionals = _.clone(experiment.conditionals).sort(byNaturalSortName);
  const parameters = _.clone(experiment.parameters).sort(byNaturalSortName);

  if (editing) {
    return (
      <tbody>
        {_.flatten([
          _.map(conditionals, (conditional) =>
            makeTableRow(
              conditional.name,
              <ConditionalInput
                assignments={assignments}
                conditional={conditional}
                disabled={submitting}
                onChange={assignmentChangeHandler(conditional.name)}
              />,
            ),
          ),
          _.map(parameters, (parameter) => {
            const props = {
              assignments,
              disabled:
                !ui.parameterEnabled(experiment, assignments, parameter.name) ||
                submitting,
              onChange: assignmentChangeHandler(parameter.name),
              parameter,
            };
            return makeTableRow(parameter.name, <ParameterInput {...props} />);
          }),
        ])}
      </tbody>
    );
  } else {
    return (
      <tbody>
        {_.map(renderOrder, (name) => (
          <TableRow
            boldName={boldName}
            key={name}
            name={name}
            value={renderedAssignments[name]}
          />
        ))}
      </tbody>
    );
  }
};

AssignmentsTableBody.propTypes = {
  assignments: schemas.Assignments,
  boldName: PropTypes.bool,
  editing: PropTypes.bool,
  experiment: schemas.Experiment,
  onChange: PropTypes.func,
  submitting: PropTypes.bool,
};

AssignmentsTableBody.defaultProps = {
  assignments: {},
  boldName: false,
  editing: false,
  onChange: _.noop,
  submitting: false,
};

export const MetadataTableBody = ({metadata}) => (
  <tbody>
    {_.chain(metadata)
      .pairs()
      .sortBy(([k]) => k)
      .map(([k, v]) => <TableRow key={k} name={k} value={v} />)
      .value()}
  </tbody>
);

export const TableCard = ({
  children,
  onClick,
  scrollable,
  measurements,
  copyObject,
}) => (
  <div
    className={classNames("table-card", {
      clickable: onClick,
      "measurement-table": measurements,
    })}
  >
    <div className="hover-glyph">
      <CircleArrowRightGlyph />
    </div>
    {copyObject ? (
      <CopyButton text={stringify(copyObject, {space: 2})} />
    ) : null}
    <table className={classNames("table", {scrollable})} onClick={onClick}>
      {children}
    </table>
  </div>
);
