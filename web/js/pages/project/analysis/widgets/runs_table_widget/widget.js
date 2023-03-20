/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import {connect} from "react-redux";

import {ConnectedRunsTable} from "../../../components/runs_table/runs_table";
import {
  setHoverInfo,
  setSelectedIds,
  setTableApi,
  updateFiltered,
} from "../../../state/dimensions_slice";

class RunsTableWidget extends React.Component {
  constructor(props) {
    super(props);

    const getRowClass = (params) => {
      if (_.includes(params.context.selectedIds, params.data.id)) {
        return "dashboard-selected-row";
      } else {
        return "";
      }
    };

    const gridOptionsOverrides = {
      pagination: false,
      onSelectionChanged: this.selectionChanged,
      onFilterChanged: this.onFilterChanged,
      getRowClass,
    };

    const tableRef = React.createRef();

    this.state = {
      gridOptionsOverrides,
      tableRef,
    };
  }

  componentDidUpdate(prevProps) {
    if (prevProps.selectedIds !== this.props.selectedIds) {
      if (!this.state.tableRef.current) {
        return;
      }
      _.defer(() =>
        this.state.tableRef.current.state.gridApi.redrawRows({force: true}),
      );
    }
  }

  onFilterChanged = () => {
    this.props.setTableApi(this.state.tableRef.current.state.gridApi);
    this.props.updateFiltered();
  };

  selectionChanged = () => {
    if (!this.state.tableRef.current) {
      return;
    }
    const rows = this.state.tableRef.current.state.gridApi.getSelectedRows();
    const rowIds = _.map(rows, (r) => r.id);
    this.props.setHoverInfo({runId: rowIds[0]});
  };

  onTableStateChanged = () => {
    if (!this.state.tableRef.current) {
      return;
    }
    this.props.updateWidget((widget) => {
      widget.state.tableState = this.state.tableRef.current.getTableState();
    });
  };

  onGridReady = () => {
    const savedTableState = this.props.widget.state.tableState;
    if (savedTableState) {
      this.state.tableRef.current.setTableState(savedTableState);
    }
  };

  render() {
    return (
      <div
        style={{
          marginLeft: -10,
          marginRight: -10,
          marginBottom: -10,
          height: "100%",
        }}
      >
        <ConnectedRunsTable
          onStateChanged={this.onTableStateChanged}
          gridOptionsOverrides={this.state.gridOptionsOverrides}
          tableRef={this.state.tableRef}
          onGridReady={this.onGridReady}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  definedFields: state.dimensions.definedFields,
  views: state.views.views,
  selectedIds: state.dimensions.selectedIds,
});

const mapDispatchToProps = {
  setSelectedIds,
  setHoverInfo,
  setTableApi,
  updateFiltered,
};

export const ConnectedRunTableWidget = connect(
  mapStateToProps,
  mapDispatchToProps,
)(RunsTableWidget);
