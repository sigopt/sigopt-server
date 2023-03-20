/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import {LocalRunsTable} from "../../components/runs_table/runs_table";

export const RunsSelect = ({
  setSelectedRunIds,
  selectedRunIds,
  runs,
  definedFields,
}) => {
  const tableRef = React.useRef(null);

  // Boostrap modals aren't full width by this point when it renders so we need to delay the autosize.
  React.useEffect(() => {
    setTimeout(
      () => tableRef.current && tableRef.current.autoSizeColumns(),
      500,
    );
  }, []);

  const onSelectionChanged = React.useCallback(() => {
    if (!tableRef.current) {
      return;
    }
    const rows = tableRef.current.state.gridApi.getSelectedRows();
    setSelectedRunIds(_.map(rows, (r) => r.id));
  }, [tableRef, setSelectedRunIds]);

  const onGridReady = React.useCallback(
    (params) => {
      if (selectedRunIds.length > 0) {
        params.api.forEachNode((node) => {
          if (_.includes(selectedRunIds, node.data.id)) {
            node.setSelected(true);
          }
        });
      }
    },
    [selectedRunIds],
  );

  const gridOptionsOverrides = {
    onSelectionChanged,
  };

  return (
    <LocalRunsTable
      runs={runs}
      definedFields={definedFields}
      gridOptionsOverrides={gridOptionsOverrides}
      tableRef={tableRef}
      onGridReady={onGridReady}
    />
  );
};
