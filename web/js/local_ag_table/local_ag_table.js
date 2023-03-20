/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import {AgGridReact} from "@ag-grid-community/react";
/* eslint-disable import/named,no-unused-vars,unused-imports/no-unused-imports */
import {
  AllCommunityModules,
  ColumnApi,
  GridApi,
  GridOptions,
} from "@ag-grid-community/all-modules";

import {areSetsEqual} from "../utils";
import {CellRenderers as frameworkComponents} from "./cell_renderers";

/* eslint-enable import/named,no-unused-vars,unused-imports/no-unused-imports */

const ROW_HEIGHT = 44;
// Reference: https://www.ag-grid.com/javascript-grid-properties/
/** @type {GridOptions} */
const defaultGridOptions = {
  autoSizePadding: 25,
  floatingFiltersHeight: ROW_HEIGHT,
  frameworkComponents,
  headerHeight: ROW_HEIGHT,
  pagination: true,
  paginationPageSize: 15,
  pivotMode: false,
  rowClassRules: {
    archived: (params) => params.data.deleted,
  },
  rowHeight: ROW_HEIGHT,
  rowSelection: "multiple",
  suppressClickEdit: true,
  suppressColumnVirtualisation: true,
  suppressMenuHide: true,
  suppressMultiSort: false,
  suppressCellSelection: true,
  suppressRowClickSelection: true,
  enableCellTextSelection: false,
};

// NOTE:
// If your expect something to be available in context you need to pass it down via props
// Specifically many of the cellRenders expect the promiseApiClient to be available
export class LocalAgTable extends React.Component {
  constructor(props) {
    super(props);

    const gridOptions = _.extend(
      {},
      defaultGridOptions,
      this.props.gridOptionsOverrides,
    );
    if (gridOptions.detailCellRendererParams) {
      gridOptions.detailCellRendererParams.detailGridOptions = _.extend(
        {},
        defaultGridOptions,
        gridOptions.detailCellRendererParams.detailGridOptions,
      );
    }

    this.debouncedNotifyStateChanged = _.debounce(this.notifyStateChanged, 500);

    this.state = {
      /** @type {ColumnApi} */
      columnApi: null,
      /** @type {GridApi} */
      gridApi: null,
      gridOptions,
    };
  }

  componentDidUpdate(prevProps, prevState) {
    if (
      prevProps.quickFilter !== this.props.quickFilter &&
      this.state.gridApi
    ) {
      this.state.gridApi.setQuickFilter(this.props.quickFilter);
    }
    if (this.state.gridApi) {
      if (
        this.state.gridApi === prevState.gridApi &&
        areSetsEqual(this.props.rowData, prevProps.rowData, "id")
      ) {
        const diff = _.difference(this.props.rowData, prevProps.rowData);
        _.each(diff, (run) => {
          const rowNode = this.state.gridApi.getRowNode(run.id);
          rowNode.setData(run);
        });
      } else {
        this.state.gridApi.setRowData(this.props.rowData);
      }
    }
  }

  onGridReady = (params) => {
    this.setState(
      {gridApi: params.api, columnApi: params.columnApi},
      this.autoSizeColumns,
    );
    params.api.setSortModel([{colId: "id", sort: "desc"}]);
    params.api.addGlobalListener(this.stateChangeListener);
    if (this.props.onGridReady) {
      this.props.onGridReady(params);
    }

    // Note: This changes internal API setting - liable to break with updates
    // Not critical,
    try {
      params.api.context.beanWrappers.tooltipManager.beanInstance.MOUSEOVER_SHOW_TOOLTIP_TIMEOUT = 500;
    } catch (e) {}
  };

  autoSizeColumns = () => {
    const columns = this.state.columnApi.getAllColumns();
    this.state.columnApi.autoSizeColumns(columns);
  };

  stateChangeListener = (eventType) => {
    const stateChangeEvents = [
      "sortChanged",
      "filterChanged",
      "columnPinned",
      "dragStopped",
      "columnVisible",
      "displayedColumnsChanged",
    ];
    if (_.contains(stateChangeEvents, eventType)) {
      this.debouncedNotifyStateChanged();
    }
  };

  notifyStateChanged = () =>
    this.props.onStateChanged && this.props.onStateChanged();

  getTableState = () => {
    if (this.state.gridApi) {
      const {gridApi, columnApi} = this.state;

      const columnState = columnApi.getColumnState();
      const columnGroupState = columnApi.getColumnGroupState();
      const sortModel = gridApi.getSortModel();
      const filterModel = gridApi.getFilterModel();

      return {columnState, columnGroupState, sortModel, filterModel};
    } else {
      return undefined;
    }
  };

  setTableState = (tableState) => {
    if (this.state.gridApi) {
      const {columnState, columnGroupState, sortModel, filterModel} =
        tableState;
      const {gridApi, columnApi} = this.state;

      columnApi.setColumnState(columnState);
      columnApi.setColumnGroupState(columnGroupState);
      gridApi.setSortModel(sortModel);
      gridApi.setFilterModel(filterModel);
    }
  };

  onStateChanged = (...params) => {
    if (this.props.onStateChanged) {
      this.props.onStateChanged(...params);
    }
  };

  getRowNodeId = _.property("id");

  render() {
    return (
      <div style={{flex: 1, width: "100%"}} className="ag-theme-material">
        {
          <AgGridReact
            context={this.props.context}
            columnDefs={this.props.columnDefs}
            modules={AllCommunityModules}
            onGridReady={this.onGridReady}
            quickFilter={this.props.quickFilter}
            getRowNodeId={this.getRowNodeId}
            {...this.state.gridOptions}
          />
        }
      </div>
    );
  }
}
