/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/history.less";

import _ from "underscore";
import React from "react";

import Component from "../../../../react/component";
import ExperimentPage from "../../page_wrapper";
import HistoryTable from "../../../../experiment/history/table";
import {ProjectRunsTable} from "../../../project/runs/project_run_table";

export default class ExperimentHistoryPage extends Component {
  sortRunColumns = (runColumns) => {
    const metaOrder = [
      "id",
      "state",
      "duration",
      "created",
      "completed",
      "deleted",
    ];
    const experimentMetrics = _.pluck(this.props.experiment.metrics, "name");
    const experimentParametersAndConditionals = _.chain([
      this.props.experiment.parameters,
      this.props.experiment.conditionals,
    ])
      .flatten()
      .pluck("name")
      .value();
    const filteredColumns = _.filter(runColumns, ({key, name}) => {
      if (key.startsWith("values.")) {
        return _.contains(experimentMetrics, name);
      }
      if (key.startsWith("assignments.")) {
        return _.contains(experimentParametersAndConditionals, name);
      }
      return _.contains(metaOrder, key);
    });
    return _.sortBy(filteredColumns, ({key}) => {
      const metaIdx = metaOrder.indexOf(key);
      if (metaIdx < 0) {
        return metaOrder.length;
      }
      return metaIdx;
    });
  };

  render() {
    const showRunsTable = Boolean(this.props.isAiExperiment);
    return (
      <ExperimentPage {...this.props} className="experiment-history-page">
        <h2 className="subtitle">History</h2>
        {!showRunsTable && (
          <a
            className="btn btn-white-border download-button"
            href={`/experiment/${this.props.experiment.id}/historydownload`}
          >
            Download Observations as CSV
          </a>
        )}
        <div className="history-table-holder">
          {showRunsTable ? (
            <ProjectRunsTable
              {...this.props}
              project={this.props.project}
              disableViews={true}
              sortColumns={this.sortRunColumns}
            />
          ) : (
            <HistoryTable {...this.props} pageSize={25} />
          )}
        </div>
      </ExperimentPage>
    );
  }
}
