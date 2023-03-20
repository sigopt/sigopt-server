/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "@ag-grid-community/core/dist/styles/ag-grid.css";
import "@ag-grid-community/core/dist/styles/ag-theme-balham.css";
import "@ag-grid-community/core/dist/styles/ag-theme-material.css";

import "./runs_table.less";

import _ from "underscore";
import React from "react";
import {connect} from "react-redux";

import Component from "../../../../react/component";
import SourcePool from "../../../../net/pool";
import {LocalAgTable} from "../../../../local_ag_table/local_ag_table";
import {SearchBar} from "../../../../component/search_bar";
import {ViewsDropdownButton} from "../views_dropdown";
import {createRunsTableColumnDefs} from "./data/run_columns";
import {createView, deleteView} from "../../state/views_slice";
import {
  setHoverInfo,
  setSelectedIds,
  setTableApi,
  updateFiltered,
} from "../../state/dimensions_slice";

export class LocalRunsTable extends Component {
  constructor(props) {
    super(props);

    let tableRef = this.props.tableRef;
    if (!this.props.tableRef) {
      tableRef = React.createRef();
    }

    this.state = {
      search: "",
      tableRef,
    };
  }

  componentDidMount() {
    this.createTableProps(this.props.definedFields, this.props.runs);
  }

  componentDidUpdate(prevProps) {
    if (prevProps.runs !== this.props.runs) {
      this.createTableProps(this.props.definedFields, this.props.runs);
    }
  }

  createTableProps = (definedFields, runs) => {
    const hasCheckpoints = _.any(runs, (run) => run.checkpoint_count > 0);
    const hasExperiments = _.any(runs, (run) => run.experiment);

    const columnDefs = createRunsTableColumnDefs(
      runs,
      definedFields,
      hasCheckpoints,
      hasExperiments,
      this.props.sortColumns,
    );

    const usersDataPool = new SourcePool((id) =>
      this.services.promiseApiClient.users(id).fetch(),
    );
    const gridOptionsOverrides = _.extend(this.props.gridOptionsOverrides);
    this.setState({gridOptionsOverrides, columnDefs, runs, usersDataPool});
  };

  onSearchChange = (e) => {
    this.setState({search: e.currentTarget.value});
  };

  createView = (viewName) => {
    if (!this.state.tableRef.current) {
      return;
    }
    const view = this.state.tableRef.current.getTableState();
    if (view) {
      this.props.createView(viewName, view);
    }
  };

  activateView = (view) => {
    if (!this.state.tableRef.current) {
      return;
    }
    this.state.tableRef.current.setTableState(view);
  };

  convertTimestamp = (timestamp) => {
    const result = new Date(timestamp * 1000);
    const strippedResult = new Date(
      result.getFullYear(),
      result.getMonth(),
      result.getDate(),
    );
    const oneDayInMs = 86400000;
    return new Date() - strippedResult >= oneDayInMs ? strippedResult : result;
  };

  convertedRunsData = () => {
    return this.state.runs.map((r) => ({
      ...r,
      created: this.convertTimestamp(r.created),
      completed: this.convertTimestamp(r.completed),
      updated: this.convertTimestamp(r.updated),
    }));
  };

  render() {
    // Need to make a copy because ag-grid changes the object
    let selectedIds = [];
    if (this.props.selectedIds) {
      selectedIds = this.props.selectedIds.slice();
    }

    const tags = {};
    if (this.props.tags) {
      _.mapObject(tags, (tag) => (tags[tag.id] = _.clone(tag)));
    }

    const exportCsv = (e) => {
      e.preventDefault();
      this.state.tableRef.current.state.gridApi.exportDataAsCsv();
    };

    return (
      <div className="run-table-wrapper">
        <div className="table-controls-row">
          {this.props.disableViews ? null : (
            <ViewsDropdownButton
              createView={this.createView}
              deleteView={this.props.deleteView}
              activateView={this.activateView}
              views={this.props.views}
            />
          )}
          <SearchBar
            onChange={this.onSearchChange}
            value={this.state.search}
            placeholder="Quick Filter ..."
          />
          <button
            className="btn basic-button-white mpm-border dropdown-toggle"
            onClick={exportCsv}
            type="button"
          >
            Download CSV
          </button>
        </div>
        <div className="run-table noGridDrag">
          {this.state.columnDefs && (
            <LocalAgTable
              context={{
                tags: tags,
                selectedIds: selectedIds,
                promiseApiClient: this.services.promiseApiClient,
                usersDataPool: this.state.usersDataPool,
                organizationId: this.props.organizationId,
              }}
              onStateChanged={this.props.onStateChanged}
              columnDefs={this.state.columnDefs}
              gridOptionsOverrides={this.state.gridOptionsOverrides}
              rowData={this.convertedRunsData()}
              quickFilter={this.state.search}
              ref={this.state.tableRef}
              onGridReady={this.onGridReady}
            />
          )}
        </div>
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  runs: state.dimensions.runs,
  definedFields: state.dimensions.definedFields,
  runsById: state.dimensions.runsById,
  tags: state.dimensions.tagsById,
  views: state.views.views,
  idIndexMap: state.dimensions.idIndexMap,
  selectedIds: state.dimensions.selectedIds,
});

const mapDispatchToProps = {
  createView,
  deleteView,
  setSelectedIds,
  setHoverInfo,
  setTableApi,
  updateFiltered,
};

export const RunsTableAdapter = (props) => {
  if (props.definedFields && props.runs) {
    return <LocalRunsTable {...props} />;
  } else {
    return null;
  }
};

export const ConnectedRunsTable = connect(
  mapStateToProps,
  mapDispatchToProps,
)(RunsTableAdapter);
