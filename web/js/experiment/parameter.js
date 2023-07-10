/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import UUID from "uuid";
import classNames from "classnames";
import {Typeahead} from "react-bootstrap-typeahead";

import ParameterConditionsInfo from "../parameter/conditions/info";
import Tooltip from "../component/tooltip";
import byNaturalSortName from "../experiment/sort_params";
import ui from "./ui";
import {InteractionStates, ParameterTypes} from "./constants";
import {RemoveRowButton} from "./buttons/remove_button";
import {Section} from "./section";
import {isDefinedAndNotNull, isUndefinedOrNull} from "../utils";

const DefaultValue = function (props) {
  const parameterInput = props.parameterInput;
  if (
    isDefinedAndNotNull(parameterInput.default_value) ||
    props.needsDefaultValue
  ) {
    if (props.editing) {
      if (parameterInput.type === ParameterTypes.CATEGORICAL) {
        if (_.isEmpty(parameterInput.categorical_values)) {
          return (
            <select className="form-control" disabled="disabled">
              <option>(no values)</option>
            </select>
          );
        } else {
          return (
            <select
              className="form-control"
              onChange={props.onChange}
              value={parameterInput.default_value}
            >
              {_.map(parameterInput.categorical_values, function (cv) {
                return (
                  <option key={cv.name} value={cv.name}>
                    {cv.name}
                  </option>
                );
              })}
            </select>
          );
        }
      } else {
        return (
          <input
            required={true}
            onChange={props.onChange}
            className="form-control"
            type="text"
            name="default_value"
            placeholder="Default value"
            value={ui.renderParamValue(
              parameterInput,
              parameterInput.default_value,
            )}
          />
        );
      }
    } else {
      return <span>{parameterInput.default_value}</span>;
    }
  } else {
    return null;
  }
};
DefaultValue.propTypes = {
  editing: PropTypes.bool.isRequired,
  needsDefaultValue: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  parameterInput: PropTypes.object.isRequired,
};

class ParameterRange extends React.Component {
  static propTypes = {
    editing: PropTypes.bool.isRequired,
    needsDefaultValue: PropTypes.bool.isRequired,
    parameterInput: PropTypes.object.isRequired,
    updateParameter: PropTypes.func.isRequired,
  };

  state = {typeaheadUUID: UUID.v4()};

  setParameterBounds = (bounds) => {
    this.props.updateParameter((p) =>
      _.extend({}, p, {bounds: _.extend({}, p.bounds, bounds)}),
    );
  };

  setCategoricalValues = (categoricalValues) => {
    this.props.updateParameter((p) => {
      const updater = {categorical_values: categoricalValues};
      if (this.props.needsDefaultValue) {
        const names = _.pluck(categoricalValues, "names");
        if (
          isDefinedAndNotNull(updater.default_value) &&
          !_.contains(names, updater.default_value)
        ) {
          updater.default_value = _.isEmpty(names) ? null : names[0];
        }
      }
      return _.extend({}, p, updater);
    });
  };

  setGridValues = (gridValues) => {
    this.props.updateParameter((p) => {
      const nonStrings = _.map(gridValues, (value) => {
        if (_.isObject(value)) {
          return Number(value.label);
        } else {
          return Number(value);
        }
      });
      const numericValues = _.filter(nonStrings, (val) => !Number.isNaN(val));
      return _.extend({}, p, {grid: numericValues});
    });
  };

  render() {
    const parameterInput = this.props.parameterInput;
    if (
      parameterInput.type !== ParameterTypes.CATEGORICAL &&
      !parameterInput.grid
    ) {
      if (this.props.editing) {
        return (
          <div className="form form-inline min-max-content">
            <div className="bounds-input-holder">
              <input
                required={true}
                onChange={(e) => this.setParameterBounds({min: e.target.value})}
                className="form-control min-input"
                type="text"
                name="min"
                placeholder="Min"
                value={ui.renderParamValue(
                  parameterInput,
                  parameterInput.bounds.min,
                )}
              />
            </div>
            <div className="bounds-input-holder">
              <input
                required={true}
                onChange={(e) => this.setParameterBounds({max: e.target.value})}
                className="form-control max-input"
                type="text"
                name="max"
                placeholder="Max (Inclusive)"
                value={ui.renderParamValue(
                  parameterInput,
                  parameterInput.bounds.max,
                )}
              />
            </div>
          </div>
        );
      } else {
        return (
          <span>
            {`[${ui.renderParamValue(
              parameterInput,
              parameterInput.bounds.min,
            )}, ${ui.renderParamValue(
              parameterInput,
              parameterInput.bounds.max,
            )}]`}
          </span>
        );
      }
    } else if (this.props.editing) {
      const isGrid = parameterInput.grid;
      if (isGrid) {
        const gridStrings = _.map(parameterInput.grid, (num) => num.toString());
        return (
          <Typeahead
            id={this.state.typeaheadUUID}
            className="categorical-value-input"
            allowNew={true}
            multiple={true}
            newSelectionPrefix="Add a grid value: "
            options={gridStrings}
            selected={gridStrings}
            placeholder="Type anything..."
            onChange={(values) => this.setGridValues(values)}
          />
        );
      } else {
        return (
          <Typeahead
            id={this.state.typeaheadUUID}
            className="categorical-value-input"
            allowNew={true}
            multiple={true}
            newSelectionPrefix="Add a categorical value: "
            labelKey="name"
            options={parameterInput.categorical_values}
            selected={parameterInput.categorical_values}
            placeholder="Type anything..."
            onChange={(values) =>
              this.setCategoricalValues(_.map(values, (v) => _.pick(v, "name")))
            }
          />
        );
      }
    } else {
      return (
        <span>
          {_.map(parameterInput.categorical_values, function (value) {
            return (
              <div key={value.name} className="categorical_value">
                {value.name}
              </div>
            );
          })}
        </span>
      );
    }
  }
}

const ParameterInputName = function (props) {
  if (props.editing && props.isNewParameter) {
    return (
      <input
        required={true}
        onChange={props.onChange}
        className="form-control"
        type="text"
        name="name"
        placeholder="Parameter Name"
        value={props.inputText || ""}
      />
    );
  } else {
    return <span>{props.inputText}</span>;
  }
};
ParameterInputName.propTypes = {
  editing: PropTypes.bool.isRequired,
  inputText: PropTypes.string,
  isNewParameter: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
};

const ParameterType = function (props) {
  const parameterInput = props.parameterInput;
  if (parameterInput.isNew && props.editing) {
    return (
      <select
        className="form-control"
        value={props.parameterInput.type || ""}
        onChange={props.onChange}
      >
        <option value={ParameterTypes.DOUBLE}>Decimal</option>
        <option value={ParameterTypes.INTEGER}>Integer</option>
        <option value={ParameterTypes.CATEGORICAL}>Categorical</option>
      </select>
    );
  } else {
    let text;
    if (parameterInput.type === ParameterTypes.DOUBLE) {
      text = "Decimal";
    } else if (parameterInput.type === ParameterTypes.CATEGORICAL) {
      text = "Categorical";
    } else if (parameterInput.type === ParameterTypes.INTEGER) {
      text = "Integer";
    } else {
      text = parameterInput.type;
    }
    return <span>{text}</span>;
  }
};
ParameterType.propTypes = {
  editing: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  parameterInput: PropTypes.object.isRequired,
};

const ParameterAddInputRow = function (props) {
  if (props.editing) {
    return (
      <tr className="button-container">
        <td className="add-button-holder">
          <a className="btn btn-secondary add-button" onClick={props.addInput}>
            Add Parameter
          </a>
        </td>
      </tr>
    );
  } else {
    return null;
  }
};

class ParameterEditRow extends React.Component {
  static propTypes = {
    create: PropTypes.bool.isRequired,
    editing: PropTypes.bool.isRequired,
    needsDefaultValue: PropTypes.bool.isRequired,
    onChange: PropTypes.func.isRequired,
    onRemove: PropTypes.func.isRequired,
    parameterInput: PropTypes.object.isRequired,
    showConditions: PropTypes.bool.isRequired,
    showDefaultValue: PropTypes.bool.isRequired,
    showGrid: PropTypes.bool.isRequired,
    showTransformations: PropTypes.bool.isRequired,
  };

  removeParameter = () => {
    this.props.onRemove(this.props.parameterInput);
  };

  updateParameter = (updater) => {
    this.props.onChange(this.props.parameterInput, updater);
  };

  render() {
    let conditionsInfo = null;
    if (this.props.create && this.props.showConditions) {
      if (_.isEmpty(this.props.parameterInput.conditions)) {
        conditionsInfo = <td>No conditions</td>;
      } else {
        conditionsInfo = (
          <td>
            <ParameterConditionsInfo
              parameterInput={this.props.parameterInput}
            />
          </td>
        );
      }
    }
    return (
      <tr data-parameter-name={this.props.parameterInput.name}>
        <td>
          <ParameterInputName
            editing={this.props.editing}
            inputText={this.props.parameterInput.name}
            isNewParameter={this.props.parameterInput.isNew}
            onChange={(e) => this.updateParameter({name: e.target.value})}
          />
        </td>
        <td>
          <ParameterType
            editing={this.props.editing}
            parameterInput={this.props.parameterInput}
            onChange={(e) =>
              this.updateParameter({type: e.target.value, default_value: null})
            }
          />
        </td>
        {this.props.showDefaultValue ? (
          <td>
            <DefaultValue
              editing={this.props.editing}
              parameterInput={this.props.parameterInput}
              needsDefaultValue={this.props.needsDefaultValue}
              onChange={(e) =>
                this.updateParameter({default_value: e.target.value})
              }
            />
          </td>
        ) : null}
        <td className="categorical-value-adder">
          <ParameterRange
            editing={this.props.editing}
            parameterInput={this.props.parameterInput}
            needsDefaultValue={this.props.needsDefaultValue}
            updateParameter={this.updateParameter}
          />
        </td>
        {this.props.showGrid &&
        isDefinedAndNotNull(this.props.parameterInput.grid) ? (
          <td>&#123;{this.props.parameterInput.grid.join(", ")}&#125;</td>
        ) : null}
        {conditionsInfo}
        {this.props.showTransformations ? (
          <td>
            {ui.isParameterTransformationNontrivial(
              this.props.parameterInput.transformation,
            )
              ? this.props.parameterInput.transformation
              : ""}
          </td>
        ) : null}
        {this.props.editing ? (
          <td className="remove-row-column">
            <RemoveRowButton removeRow={this.removeParameter} />
          </td>
        ) : null}
      </tr>
    );
  }
}

class ParametersTable extends React.Component {
  needsDefaultValue = (parameterInput) => {
    if (this.props.create) {
      return false;
    }
    const initialParameters = (this.props.experiment || {}).parameters || [];
    const dontNeedDefaultValues = _.filter(initialParameters, (p) =>
      isUndefinedOrNull(p.default_value),
    );
    return _.all(dontNeedDefaultValues, (p) => p.name !== parameterInput.name);
  };

  render() {
    const showDefaultValue = _.any(
      this.props.parameters,
      (p) => isDefinedAndNotNull(p.default_value) || this.needsDefaultValue(p),
    );
    const showGrid = _.any(this.props.parameters, (p) => p.grid);
    const showConditions =
      !this.props.create && !_.isEmpty(this.props.experimentInput.conditionals);
    const sortedParameters = _.clone(this.props.parameters).sort(
      byNaturalSortName,
    );
    const showTransformations = _.chain(this.props.parameters)
      .pluck("transformation")
      .any(ui.isParameterTransformationNontrivial)
      .value();

    return (
      <table
        className={classNames({
          table: true,
          "experiment-edit-table": true,
          empty: _.isEmpty(this.props.parameters),
        })}
      >
        <thead>
          <tr>
            <th>
              <Tooltip tooltip="Parameters are uniquely named, so you can identify them.">
                Name
              </Tooltip>
            </th>
            <th>
              <Tooltip
                tooltip={
                  "Parameters can be integers or decimals, which are numeric values." +
                  " They can also be categorical, which means they take one of a fixed list of values" +
                  " (such as true/false)."
                }
              >
                Type
              </Tooltip>
            </th>
            {showDefaultValue ? <th>Default Value</th> : null}
            <th>
              <span className="range-label">
                <Tooltip
                  tooltip={
                    "We'll search over the range of values you provide to optimize each parameter. " +
                    "By picking a tighter range, you'll find the optimal parameters faster."
                  }
                >
                  Range
                </Tooltip>
              </span>
            </th>
            {showGrid ? <th>Grid</th> : null}
            {showConditions ? <th>Conditions</th> : null}
            {showTransformations ? <th>Transformations</th> : null}
            {this.props.editing ? <th className="remove-row-column" /> : null}
          </tr>
        </thead>
        <tbody>
          {_.map(
            this.props.create ? this.props.parameters : sortedParameters,
            (p) => (
              <ParameterEditRow
                create={this.props.create}
                editing={
                  this.props.editing ? this.props.canEditParameters() : null
                }
                experimentInput={this.props.experimentInput}
                key={this.props.parameterKey(p)}
                needsDefaultValue={this.needsDefaultValue(p)}
                onChange={this.props.setParameter}
                onRemove={this.props.removeParameter}
                parameterInput={p}
                rowType="parameter"
                showConditions={showConditions}
                showGrid={showGrid}
                showDefaultValue={showDefaultValue}
                showTransformations={showTransformations}
              />
            ),
          )}
          <ParameterAddInputRow
            addInput={this.props.addParameter()}
            editing={this.props.editing ? this.props.canEditParameters() : null}
            numColumns={5}
          />
        </tbody>
      </table>
    );
  }
}

export const ParameterSection = function (props) {
  const create = props.interactionState === InteractionStates.CREATE;
  const editing = ui.inputInteraction(props.interactionState);
  return (
    <Section
      infoClassName="experiment-parameter-info"
      heading={
        <Tooltip
          tooltip={
            "Parameters are the values that might affect the metric you are trying to optimize. " +
            "We'll tune these parameters to search for the optimal values."
          }
        >
          Parameters
        </Tooltip>
      }
      sectionBody={
        <ParametersTable
          addParameter={props.addParameter}
          canEditParameters={props.canEditParameters}
          create={create}
          editing={editing}
          experiment={props.experiment}
          experimentInput={props.experimentInput}
          parameterKey={props.parameterKey}
          parameters={props.experimentInput.parameters}
          removeParameter={props.removeParameter}
          setParameter={props.setParameter}
        />
      }
    />
  );
};
