/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */
import "../runs_table.less";

import _ from "underscore";
import React from "react";

import ModalForm from "../../../../../component/modal/form";
import {CellRendererNames} from "../../../../../local_ag_table/cell_renderers";
import {LocalAgTable} from "../../../../../local_ag_table/local_ag_table";

/* eslint-disable import/named,no-unused-vars,unused-imports/no-unused-imports */

export class CreateCheckpointsModal extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
    this._modal = React.createRef();
  }

  show = () => this._modal.current && this._modal.current.show();

  render() {
    return (
      <ModalForm
        cancelButtonLabel="Close"
        title="Checkpoints Table"
        ref={this._modal}
      >
        <LocalCheckpointsTable
          run_id={this.props.run_id}
          promiseApiClient={this.props.promiseApiClient}
        />
      </ModalForm>
    );
  }
}

class LocalCheckpointsTable extends React.Component {
  constructor(props) {
    super(props);

    let tableRef = this.props.tableRef;
    if (!this.props.tableRef) {
      tableRef = React.createRef();
    }

    this.state = {
      tableRef,
      checkpoints: [],
    };
  }
  // move over to sigopt server once checkpoint table is done
  // experiment_table.js in siteadmin for pageFetcher stuff
  // this.props.promiseApiClient.trainingRuns(run.id).checkpoints().exhaustivelyPage().call(
  // this.test(),
  // {},
  // {
  // },
  // (response) => {
  // if(isDefinedAndNotNull(response)) {
  // this.setState({checkpoints: response.data})
  // }
  // };

  componentDidMount() {
    const getCheckpointsForRun = (id) => {
      return this.checkpointsPromise.call(
        {},
        {
          id: id,
        },
      );
    };

    getCheckpointsForRun(this.props.run_id).then((value) => {
      this.setState({checkpoints: value});
    });
  }

  checkpointColumnDefs(checkpoints) {
    const metricCheckpointValueGetter = (params) => {
      const metricName = params.colDef.field;
      const metric = _.find(params.data.values, (v) => v.name === metricName);
      return metric && metric.value;
    };

    const staticColumnDefs = [
      {
        field: "id",
        width: 100,
        minWidth: 100,
        sortable: true,
        valueGetter: (params) => {
          return Number(params.data.id);
        },
      },
      {
        field: "created",
        displayName: "Created",
        sortable: true,
        cellRenderer: CellRendererNames.timestamp,
        minWidth: 60,
        width: 100,
        type: "numericColumn",
        valueGetter: (params) => {
          const result = new Date(params.data.created * 1000);
          const strippedResult = new Date(
            result.getFullYear(),
            result.getMonth(),
            result.getDate(),
          );
          const oneDayInMs = 86400000;
          return new Date() - strippedResult >= oneDayInMs
            ? strippedResult
            : result;
        },
      },
    ];
    const allMetricNames = _.chain(checkpoints)
      .map((c) => _.pluck(c.values, "name"))
      .flatten()
      .unique()
      .value();

    const metricColumnDefs = _.map(allMetricNames, (name) => ({
      valueGetter: metricCheckpointValueGetter,
      field: name,
      headerName: name,
      type: "numericColumn",
      sortable: true,
      resizable: true,
    }));

    return [...staticColumnDefs, ...metricColumnDefs];
  }

  checkpointsPromise = (args, params, success, error) => {
    return this.props.promiseApiClient
      .trainingRuns(args.id)
      .checkpoints()
      .exhaustivelyPage()
      .then(success, error);
  };

  render() {
    return (
      <div className="run-table-wrapper">
        <div className="run-table">
          <LocalAgTable
            // context={{
            // promiseApiClient: this.props.promiseApiClient,
            // }}
            // onStateChanged={this.props.onStateChanged}
            columnDefs={this.checkpointColumnDefs()}
            // gridOptionsOverrides={this.state.gridOptionsOverrides}
            // quickFilter={this.state.search}
            rowData={this.state.checkpoints}
            ref={this.state.tableRef}
            // onGridReady={this.onGridReady}
          />
        </div>
      </div>
    );
  }
}
