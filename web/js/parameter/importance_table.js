/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import CustomTooltip from "../component/custom_tooltip";
import ProgressBar from "../component/progress_bar";
import schemas from "../react/schemas";
import ui from "../experiment/ui";
import {NULL_METRIC_NAME} from "../constants";

class ImportanceTable extends React.Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    metricImportances: PropTypes.arrayOf(schemas.MetricImportance).isRequired,
  };

  state = {
    sortKey:
      _.first(_.sortBy(ui.mostImportantMetrics(this.props.experiment), "name"))
        .name || NULL_METRIC_NAME,
    sortReversed: true,
  };

  onSort = (newSortKey, prevSortKey, prevSortReversed) => {
    const newSortReversed =
      newSortKey === prevSortKey
        ? !prevSortReversed
        : newSortKey !== "parameter_name";
    this.setState({sortKey: newSortKey, sortReversed: newSortReversed});
  };

  render() {
    const hasMultipleMetrics = ui.isParetoOptimizedExperiment(
      this.props.experiment,
    );
    const metrics = _.chain(ui.mostImportantMetrics(this.props.experiment))
      .map((m) => ({name: m.name || NULL_METRIC_NAME}))
      .sortBy("name")
      .value();

    const mostImportantMetricNames = _.pluck(metrics, "name");
    const mostImportantMetricImportances = _.filter(
      this.props.metricImportances,
      (i) => _.contains(mostImportantMetricNames, i.metric || NULL_METRIC_NAME),
    );

    const importances = _.chain(this.props.experiment.parameters)
      .map((p) => {
        const imp = {parameter_name: p.name};
        _.each(mostImportantMetricImportances, (i) => {
          imp[i.metric || NULL_METRIC_NAME] = i.importances[p.name];
        });
        return imp;
      })
      .sortBy(this.state.sortKey)
      .value();

    if (this.state.sortReversed) {
      importances.reverse();
    }

    return (
      <div className="table-responsive">
        <table className="table">
          <thead>
            {hasMultipleMetrics ? (
              <tr>
                <th>
                  <a
                    className={classNames(
                      "multiple-metric-sort-link",
                      this.state.sortKey === "parameter_name" &&
                        (this.state.sortReversed ? "descending" : "ascending"),
                    )}
                    onClick={() =>
                      this.onSort(
                        "parameter_name",
                        this.state.sortKey,
                        this.state.sortReversed,
                      )
                    }
                  >
                    Name
                  </a>
                </th>
                <th>
                  Importance
                  {_.map(metrics, (m) => (
                    <a
                      className={classNames(
                        "metric-header",
                        "multiple-metric-sort-link",
                        this.state.sortKey === m.name &&
                          (this.state.sortReversed
                            ? "descending"
                            : "ascending"),
                      )}
                      key={m.name}
                      onClick={() =>
                        this.onSort(
                          m.name,
                          this.state.sortKey,
                          this.state.sortReversed,
                        )
                      }
                    >
                      {m.name}
                    </a>
                  ))}
                </th>
              </tr>
            ) : (
              <tr>
                <th>Name</th>
                <th>Importance</th>
              </tr>
            )}
          </thead>
          <tbody>
            {_.map(importances, (i) => (
              <tr key={i.parameter_name}>
                <td title={i.parameter_name}>{i.parameter_name}</td>
                <td>
                  {_.map(metrics, (m) =>
                    hasMultipleMetrics ? (
                      <div key={m.name} className="metric-holder">
                        <CustomTooltip tooltip={m.name}>
                          <div className="tooltip-trigger">
                            <ProgressBar width={i[m.name]} />
                          </div>
                        </CustomTooltip>
                      </div>
                    ) : (
                      <ProgressBar key={m.name} width={i[m.name]} />
                    ),
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
}

export default ImportanceTable;
