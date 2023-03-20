/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import AxisSelector from "../chart/axis_selector";
import {AxisTypes} from "../chart/constants";
import {ChartTypes, chartTypesProp} from "./unified_constants";
import {Dropdown, DropdownItem} from "../component/dropdown";
import {ScaleSelector} from "../chart/scale_selector";
import {unifiedChartArgsProp} from "./unified_chart_args";

const chartTypeOptions = _.values(ChartTypes);

export class UnifiedChartTypeSelector extends React.Component {
  static propTypes = {
    onSelect: PropTypes.func.isRequired,
    options: PropTypes.arrayOf(chartTypesProp.isRequired),
    selected: chartTypesProp.isRequired,
  };

  render() {
    return (
      <div className="param-select-line">
        <label>chart type:</label>
        <Dropdown
          buttonClassName="btn btn-default"
          label={this.props.selected.label}
        >
          {_.map(this.props.options || chartTypeOptions, (type) => (
            <DropdownItem key={type.key}>
              <a onClick={() => this.props.onSelect(type)}>{type.label}</a>
            </DropdownItem>
          ))}
        </Dropdown>
      </div>
    );
  }
}

export class UnifiedAxisSelector extends React.Component {
  static propTypes = {
    args: unifiedChartArgsProp,
    logScaleSelected: PropTypes.bool,
    name: PropTypes.string.isRequired,
    onSelect: PropTypes.func.isRequired,
    onSelectScale: PropTypes.func.isRequired,
    options: PropTypes.arrayOf(PropTypes.oneOf(_.values(AxisTypes))),
    selected: PropTypes.string,
  };

  render() {
    const hasType = (type) => _.contains(this.props.options, type);
    return (
      <div className="param-select-line">
        <label>
          {this.props.name === "highlight"
            ? "Highlight:"
            : `${this.props.name} axis:`}
        </label>
        <AxisSelector
          experiment={this.props.args.experiment}
          metadataKeys={this.props.args.metadataKeys}
          observations={this.props.args.observations}
          onSelect={this.props.onSelect}
          selected={this.props.selected}
          showMetadata={hasType(AxisTypes.METADATA)}
          showConstrainedMetrics={hasType(AxisTypes.CONSTRAINED_METRIC)}
          showOptimizedMetrics={hasType(AxisTypes.OPTIMIZED_METRIC)}
          showParameters={hasType(AxisTypes.PARAMETER)}
          showStoredMetrics={hasType(AxisTypes.STORED_METRIC)}
        />
        <ScaleSelector
          experiment={this.props.args.experiment}
          onSelect={this.props.onSelectScale}
          selectedAxis={this.props.selected}
          logScaleSelected={this.props.logScaleSelected}
        />
      </div>
    );
  }
}

export class UnifiedCheckboxSelector extends React.Component {
  static propTypes = {
    checked: PropTypes.bool.isRequired,
    label: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired,
  };

  render() {
    return (
      <div className="param-select-line">
        <label>{`${this.props.label}:`}</label>
        <input
          type="checkbox"
          checked={this.props.checked}
          onChange={() => this.props.onChange()}
        />
      </div>
    );
  }
}
