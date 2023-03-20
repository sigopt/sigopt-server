/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import schemas from "../react/schemas";
import ui from "./ui";

export const ConditionalInput = ({
  assignments,
  conditional,
  disabled,
  onChange,
}) => (
  <select
    name={conditional.name}
    className="form-control param data-input"
    disabled={disabled}
    onChange={onChange}
    value={ui.renderInputValue(assignments[conditional.name])}
  >
    {_.map(conditional.values, (value) => (
      <option value={value} name={value} key={value}>
        {value}
      </option>
    ))}
  </select>
);

ConditionalInput.propTypes = {
  assignments: schemas.Assignments,
  conditional: schemas.Conditional.isRequired,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
};

ConditionalInput.defaultProps = {
  assignments: {},
  disabled: false,
};

const CategoricalInput = ({assignments, disabled, onChange, parameter}) => (
  <select
    name={parameter.name}
    className="form-control param data-input"
    data-name={parameter.name}
    disabled={disabled}
    onChange={onChange}
    value={ui.renderInputValue(assignments[parameter.name])}
  >
    {_.map(parameter.categorical_values, (value) => (
      <option value={value.name} name={value.name} key={value.name}>
        {value.name}
      </option>
    ))}
  </select>
);

CategoricalInput.propTypes = {
  assignments: schemas.Assignments,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  parameter: schemas.Parameter.isRequired,
};

CategoricalInput.defaultProps = {
  assignments: {},
  disabled: false,
};

const GridInput = ({assignments, disabled, onChange, parameter}) => (
  <select
    name={parameter.name}
    className="form-control param data-input"
    data-name={parameter.name}
    disabled={disabled}
    onChange={onChange}
    value={ui.renderInputValue(assignments[parameter.name])}
  >
    {_.map(parameter.grid, (value) => (
      <option value={value} name={value} key={value}>
        {value}
      </option>
    ))}
  </select>
);

const NumericalInput = ({assignments, disabled, onChange, parameter}) => {
  const intParam = parameter.type === "int";
  const step = intParam
    ? 1
    : (parameter.bounds.max - parameter.bounds.min) / 100;
  const value = assignments[parameter.name];
  const renderBound = (bound) =>
    ui.renderParamValue(parameter, parameter.bounds[bound], true);
  return (
    <input
      className="form-control param data-input"
      disabled={disabled}
      min={parameter.bounds.min}
      max={parameter.bounds.max}
      name={parameter.name}
      onChange={onChange}
      placeholder={`Range [${renderBound("min")}, ${renderBound("max")}]`}
      step={step}
      type="number"
      value={ui.renderInputValue(value)}
    />
  );
};

NumericalInput.propTypes = {
  assignments: schemas.Assignments,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  parameter: schemas.Parameter.isRequired,
};

NumericalInput.defaultProps = {
  assignments: {},
  disabled: false,
};

export const ParameterInput = (props) => {
  const parameter = props.parameter;
  if (parameter.grid) {
    return <GridInput {...props} />;
  } else if (parameter.categorical_values) {
    return <CategoricalInput {...props} />;
  } else {
    return <NumericalInput {...props} />;
  }
};
ParameterInput.propTypes = {
  assignments: schemas.Assignments,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  parameter: schemas.Parameter.isRequired,
};

export const TaskInput = ({currentTask, tasks, disabled, onChange}) => (
  <select
    name={currentTask.name}
    className="form-control param data-input"
    data-name={currentTask.name}
    disabled={disabled}
    onChange={onChange}
    value={currentTask.name}
  >
    {_.chain(tasks)
      .map((t) => (
        <option value={t.name} name={t.name} key={t.name}>
          {ui.renderTask(t)}
        </option>
      ))
      .sortBy("cost")
      .value()}
  </select>
);

TaskInput.propTypes = {
  currentTask: schemas.Task.isRequired,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  tasks: PropTypes.arrayOf(schemas.Task),
};

TaskInput.defaultProps = {
  disabled: false,
  tasks: {},
};
