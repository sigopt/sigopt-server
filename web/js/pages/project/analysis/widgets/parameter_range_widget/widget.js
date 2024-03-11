/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import classNames from "classnames";
import stringify from "fast-json-stable-stringify";
import {connect} from "react-redux";

import {CopyButton} from "../../../../../component/code_block";
import {
  isDefinedAndNotNull,
  naturalStringCompare,
  renderNumber,
} from "../../../../../utils";

const Property = ({name, value}) => (
  <div className="parameter-property">
    {name}: {value}
  </div>
);

const CategoricalProperties = ({info}) => (
  <Property
    name="categorical_values"
    value={stringify(info.categorical_values)}
  />
);

const NumericProperties = ({info}) => [
  <Property key="min" name="min" value={renderNumber(info.bounds.min, 6)} />,
  <Property key="max" name="max" value={renderNumber(info.bounds.max, 6)} />,
];

const properties = {
  categorical: CategoricalProperties,
  double: NumericProperties,
  int: NumericProperties,
};

class ParameterRow extends React.Component {
  onChange = () =>
    this.props.setSelected(this.props.info, !this.props.selected);

  render() {
    const {info, selected} = this.props;
    const Properties = properties[info.type];
    return (
      <tr className={classNames({selected})}>
        <td>
          <input checked={selected} onChange={this.onChange} type="checkbox" />
        </td>
        <td>{info.name}</td>
        <td>{info.type}</td>
        <td>
          <Properties info={info} />
        </td>
      </tr>
    );
  }
}

export const getParameterInfo = (dims) => {
  return _.chain(dims)
    .map((dim) => {
      if (dim.groupType !== "PARAMETER") {
        return null;
      }
      const nonNullValues = _.filter(dim.values, isDefinedAndNotNull);
      if (_.isEmpty(nonNullValues)) {
        return null;
      }
      const name = dim.label;
      if (_.all(nonNullValues, _.isNumber)) {
        const floatingPoint = _.any(nonNullValues, (value) => value % 1 !== 0);
        return {
          name,
          type: floatingPoint ? "double" : "int",
          bounds: {
            min: _.min(nonNullValues),
            max: _.max(nonNullValues),
          },
        };
      }
      return {
        name,
        type: "categorical",
        categorical_values: _.chain(nonNullValues)
          .map((v) => v.toString())
          .uniq()
          .sort(naturalStringCompare)
          .value(),
      };
    })
    .filter()
    .sort((p1, p2) => naturalStringCompare(p1.name, p2.name))
    .value();
};

class ParameterRangeWidget extends React.Component {
  state = {parameterInfo: null, selectedParameters: {}};

  componentDidMount() {
    this.setParameterInfoFromDims();
  }

  componentDidUpdate(prevProps) {
    if (this.props.dims !== prevProps.dims) {
      this.setParameterInfoFromDims();
    }
  }

  setParameterInfoFromDims = () => {
    this.setState({parameterInfo: getParameterInfo(this.props.dims)});
  };

  setSelected = (parameter, selected) =>
    this.setState((state) => {
      state.selectedParameters[parameter.name] = selected;
      return state;
    });

  render() {
    const isParameterUseful = (info) =>
      info.type === "categorical"
        ? _.size(info.categorical_values) > 1
        : info.bounds.max > info.bounds.min;
    const isParameterSelected = (info) =>
      _.has(this.state.selectedParameters, info.name)
        ? this.state.selectedParameters[info.name]
        : isParameterUseful(info);
    const filteredParameters = _.filter(
      this.state.parameterInfo,
      isParameterSelected,
    );
    return (
      <div className="widget parameter-ranges">
        <CopyButton
          text={stringify(filteredParameters, {space: 2})}
          title="Click to copy selected parameters"
        />
        <table className="table">
          <thead>
            <tr>
              <th />
              <th>Name</th>
              <th>Type</th>
              <th>Properties</th>
            </tr>
          </thead>
          <tbody>
            {_.map(this.state.parameterInfo, (info) => (
              <ParameterRow
                key={info.name}
                info={info}
                selected={isParameterSelected(info)}
                setSelected={this.setSelected}
              />
            ))}
          </tbody>
        </table>
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  dims: state.dimensions.dimensions,
});

export const ConnectedParameterRangeWidget =
  connect(mapStateToProps)(ParameterRangeWidget);

export const ParameterRangeWidgetBuilder = {
  type: "ParameterRange",
  layout: {w: 2, h: 6, minH: 4, minW: 1},
  state: {title: "Suggested Parameters"},
};
