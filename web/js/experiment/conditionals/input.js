/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import UUID from "uuid";
import classNames from "classnames";
import {Typeahead} from "react-bootstrap-typeahead";

import {AddButton, RemoveButton} from "../../component/buttons";
import {editKey} from "../../utils";

class ConditionalValueInput extends React.Component {
  state = {
    typeaheadUUID: UUID.v4(),
  };

  onChange = (parameters) => {
    const selected = this.getSelected();
    const newSelection = _.pluck(parameters, "editKey");
    const oldSelection = _.pluck(selected, "editKey");
    _.map(
      _.reject(parameters, (p) => _.contains(oldSelection, p.editKey)),
      this.props.onAddCondition,
    );
    _.map(
      _.reject(selected, (p) => _.contains(newSelection, p.editKey)),
      this.props.onRemoveCondition,
    );
  };

  getSelected = () => {
    const key = this.props.conditional.editKey;
    return _.filter(
      this.props.experimentInput.parameters,
      (p) =>
        _.has(p.conditions, key) &&
        _.contains(p.conditions[key], this.props.value.editKey),
    );
  };

  render() {
    const value = this.props.value;
    const selected = this.getSelected();
    const options = _.reject(this.props.experimentInput.parameters, (p) =>
      _.isEmpty(p.name),
    );
    return (
      <div className="form-group">
        <label className="value-label">Condition</label>
        <div className="remove-value-button-holder">
          <RemoveButton onClick={this.props.onRemoveValue} />
        </div>
        <div className="conditional-value-input-holder">
          <input
            required={true}
            onChange={(e) => this.props.onChangeValueName(e.target.value)}
            className="form-control"
            type="text"
            name="value"
            placeholder="value"
            value={value.name}
          />
        </div>
        <div
          className={classNames("parameter-input-holder", {
            enabled: !_.isEmpty(options),
          })}
        >
          <Typeahead
            id={this.state.typeaheadUUID}
            disabled={_.isEmpty(options)}
            multiple={true}
            labelKey="name"
            options={options}
            selected={selected}
            onChange={this.onChange}
            placeholder="Pick parameters..."
          />
        </div>
      </div>
    );
  }
}

class ExperimentConditionalsInputRow extends React.Component {
  render() {
    const conditional = this.props.conditional;
    return (
      <div className="form-horizontal experiment-conditionals-input-row">
        <div className="form-group">
          <label className="name-label">Name</label>
          <div className="remove-conditional-button-holder">
            <RemoveButton
              /* eslint-disable-next-line react/jsx-no-bind */
              onClick={() => this.props.onRemoveConditional(conditional)}
            />
          </div>
          <div className="name-input-holder">
            <input
              required={true}
              onChange={(e) =>
                this.props.onChangeName(conditional, e.target.value)
              }
              className="form-control"
              type="text"
              name="name"
              placeholder="name"
              value={conditional.name}
            />
          </div>
        </div>
        {_.map(conditional.values, (v) => (
          <ConditionalValueInput
            key={v.editKey || v.name}
            value={v}
            conditional={conditional}
            experimentInput={this.props.experimentInput}
            onRemoveValue={_.partial(this.props.onRemoveValue, conditional, v)}
            onChangeValueName={_.partial(
              this.props.onChangeValueName,
              conditional,
              v,
            )}
            onAddCondition={_.partial(
              this.props.onAddCondition,
              conditional,
              v,
            )}
            onRemoveCondition={_.partial(
              this.props.onRemoveCondition,
              conditional,
              v,
            )}
          />
        ))}
        <div className="form-group">
          <div className="add-value-button-holder">
            <AddButton
              onClick={_.partial(this.props.onAddValue, conditional)}
            />
          </div>
        </div>
      </div>
    );
  }
}

export class ConditionalsCreate extends React.Component {
  onChangeName = (conditional, name) => {
    this.props.onChangeConditional(conditional, (c) =>
      _.extend({}, c, {name: name}),
    );
  };

  onAddValue = (conditional) => {
    this.props.onChangeConditional(conditional, (c) =>
      _.extend({}, c, {
        values: c.values.concat({name: "", editKey: editKey()}),
      }),
    );
  };

  onRemoveValue = (conditional, value) => {
    const key = value.editKey || value.name;
    this.props.onChangeConditional(conditional, (c) =>
      _.extend({}, c, {
        values: _.reject(c.values, (v) => (v.editKey || v.name) === key),
      }),
    );
  };

  onChangeValueName = (conditional, value, name) => {
    // TODO: they'll never not have an edit key...
    const key = value.editKey || value.name;
    this.props.onChangeConditional(conditional, (c) => {
      const newValues = _.map(c.values, (v) =>
        (v.editKey || v.name) === key ? _.extend({}, v, {name: name}) : v,
      );
      return _.extend({}, c, {values: newValues});
    });
  };

  onAddCondition = (conditional, value, parameter) => {
    this.props.setParameter(parameter, (p) => {
      let newConditions;
      if (_.has(p.conditions, conditional.editKey)) {
        newConditions = _.mapObject(p.conditions, (values, k) =>
          k === conditional.editKey
            ? _.without(values, value.editKey).concat(value.editKey)
            : values,
        );
      } else {
        newConditions = _.extend({}, p.conditions, {
          [conditional.editKey]: [value.editKey],
        });
      }
      return _.extend({}, p, {conditions: newConditions});
    });
  };

  onRemoveCondition = (conditional, value, parameter) => {
    this.props.setParameter(parameter, (p) => {
      if (p) {
        let newConditions;

        if (_.has(p.conditions, conditional.editKey)) {
          const newValues = _.without(
            p.conditions[conditional.editKey],
            value.editKey,
          );
          if (_.isEmpty(newValues)) {
            newConditions = _.omit(p.conditions, conditional.editKey);
          } else {
            newConditions = _.mapObject(p.conditions, (values, k) =>
              k === conditional.editKey ? newValues : values,
            );
          }
        } else {
          newConditions = p.conditions;
        }

        return _.extend({}, p, {conditions: newConditions});
      }

      return undefined;
    });
  };

  render() {
    const conditionals = this.props.experimentInput.conditionals;
    return (
      <div className="experiment-conditionals-input">
        {_.map(conditionals, (conditional) => (
          <ExperimentConditionalsInputRow
            key={conditional.editKey || conditional.name}
            conditional={conditional}
            experimentInput={this.props.experimentInput}
            onChangeName={this.onChangeName}
            onAddValue={this.onAddValue}
            onRemoveValue={this.onRemoveValue}
            onRemoveConditional={this.props.onRemoveConditional}
            onChangeValueName={this.onChangeValueName}
            onAddCondition={this.onAddCondition}
            onRemoveCondition={this.onRemoveCondition}
          />
        ))}
        <div className="experiment-conditionals-input-row">
          <span
            className="btn btn-secondary add-button"
            onClick={this.props.onAddConditional}
          >
            Add Conditional
          </span>
        </div>
      </div>
    );
  }
}
