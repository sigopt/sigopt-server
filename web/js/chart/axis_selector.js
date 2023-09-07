/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import schemas from "../react/schemas";
import ui from "../experiment/ui";
import {AxisTypes} from "./constants";
import {Dropdown, DropdownHeader, DropdownItem} from "../component/dropdown";
import {NULL_METRIC_NAME} from "../constants";

// TODO: what if there's only one parameter to select from?
class AxisSelector extends React.Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    metadataKeys: PropTypes.arrayOf(PropTypes.string.isRequired),
    onSelect: PropTypes.func.isRequired,
    selected: PropTypes.string,
    showConstrainedMetrics: PropTypes.bool,
    showMetadata: PropTypes.bool,
    showOptimizedMetrics: PropTypes.bool,
    showParameters: PropTypes.bool,
    showStoredMetrics: PropTypes.bool,
  };

  getMetricKeys = (metrics) =>
    _.map(metrics, (m) => m.name || NULL_METRIC_NAME);

  render() {
    const experiment = this.props.experiment;
    const metadataKeys = this.props.metadataKeys || [];
    const optimizedMetricKeys = this.getMetricKeys(
      ui.optimizedMetrics(this.props.experiment),
    );
    const constrainedMetricKeys = this.getMetricKeys(
      ui.constrainedMetrics(this.props.experiment),
    );
    const storedMetricKeys = this.getMetricKeys(
      ui.storedMetrics(this.props.experiment),
    );
    const showOptimizedMetrics =
      this.props.showOptimizedMetrics &&
      (optimizedMetricKeys.length > 0 || null);
    const showConstrainedMetrics =
      this.props.showConstrainedMetrics &&
      (constrainedMetricKeys.length > 0 || null);
    const showStoredMetrics =
      this.props.showStoredMetrics && (storedMetricKeys.length > 0 || null);
    const showMetadata =
      this.props.showMetadata && (metadataKeys.length > 0 || null);
    const showParameters = this.props.showParameters;
    const showConditionals =
      showParameters && !_.isEmpty(this.props.experiment.conditionals);

    return (
      <Dropdown buttonClassName="btn btn-default" label={this.props.selected}>
        {showParameters ? <DropdownHeader>Parameters</DropdownHeader> : null}
        {showParameters
          ? _.map(experiment.parameters, (p) => (
              <DropdownItem key={p.name}>
                <a
                  onClick={() =>
                    this.props.onSelect(p.name, AxisTypes.PARAMETER)
                  }
                >
                  {p.name}
                </a>
              </DropdownItem>
            ))
          : null}
        {showOptimizedMetrics ? (
          <DropdownHeader>Optimized Metrics</DropdownHeader>
        ) : null}
        {showOptimizedMetrics
          ? _.map(optimizedMetricKeys, (metricKey) => (
              <DropdownItem key={metricKey || ""}>
                <a
                  onClick={() =>
                    this.props.onSelect(metricKey, AxisTypes.OPTIMIZED_METRIC)
                  }
                >
                  {metricKey}
                </a>
              </DropdownItem>
            ))
          : null}
        {showConstrainedMetrics ? (
          <DropdownHeader>Constrained Metrics</DropdownHeader>
        ) : null}
        {showConstrainedMetrics
          ? _.map(constrainedMetricKeys, (metricKey) => (
              <DropdownItem key={metricKey || ""}>
                <a
                  onClick={() =>
                    this.props.onSelect(metricKey, AxisTypes.CONSTRAINED_METRIC)
                  }
                >
                  {metricKey}
                </a>
              </DropdownItem>
            ))
          : null}
        {showStoredMetrics ? (
          <DropdownHeader>Stored Metrics</DropdownHeader>
        ) : null}
        {showStoredMetrics
          ? _.map(storedMetricKeys, (metricKey) => (
              <DropdownItem key={metricKey || ""}>
                <a
                  onClick={() =>
                    this.props.onSelect(metricKey, AxisTypes.STORED_METRIC)
                  }
                >
                  {metricKey}
                </a>
              </DropdownItem>
            ))
          : null}
        {showConditionals ? (
          <DropdownHeader>Conditionals</DropdownHeader>
        ) : null}
        {showConditionals
          ? _.map(experiment.conditionals, (c) => (
              <DropdownItem key={c.name}>
                <a
                  onClick={() =>
                    this.props.onSelect(c.name, AxisTypes.CONDITIONAL)
                  }
                >
                  {c.name}
                </a>
              </DropdownItem>
            ))
          : null}
        {showMetadata ? <DropdownHeader>Metadata</DropdownHeader> : null}
        {showMetadata
          ? _.map(metadataKeys, (metadataKey) => (
              <DropdownItem key={metadataKey || ""}>
                <a
                  onClick={() =>
                    this.props.onSelect(metadataKey, AxisTypes.METADATA)
                  }
                >
                  {metadataKey}
                </a>
              </DropdownItem>
            ))
          : null}
      </Dropdown>
    );
  }
}

export default AxisSelector;
