/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {get as lodashGet} from "lodash";

import SetFilter from "./custom_filters/set_filter";
import TagFilter from "./custom_filters/tag_filter";

const lodashValueGetter = (params) =>
  lodashGet(params.data, params.colDef.field);

// TODO(SN-1047): make "type columns" (see column properities in docs)
// Reference: https://www.ag-grid.com/javascript-grid-column-properties/
export const defaultColumnSettings = {
  menuTabs: ["filterMenuTab", "generalMenuTab"],
  minWidth: 60,
  resizable: true,
  sortable: true,
  suppressMenu: false,
  valueGetter: lodashValueGetter,
};

export const AG_COLUMN_TYPES = {
  NUMERIC: "numericColumn",
};

export const AG_FILTER_TYPES = {
  NUMERIC: "agNumberColumnFilter",
  STRING: "agTextColumnFilter",
  DATE: "agDateColumnFilter",
};

const CustomFilters = {
  SetFilter,
  TagFilter,
};

export const CUSTOM_FILTER_TYPES = _.object(
  _.map(_.keys(CustomFilters), (k) => [k, k]),
);
