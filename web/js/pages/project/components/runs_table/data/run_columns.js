/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {get as lodashGet} from "lodash";

import {
  AG_COLUMN_TYPES,
  AG_FILTER_TYPES,
  CUSTOM_FILTER_TYPES,
  defaultColumnSettings,
} from "../../../../../local_ag_table/lib";
import {CellRendererNames} from "../../../../../local_ag_table/cell_renderers";
import {coalesce, isDefinedAndNotNull} from "../../../../../utils";

const removeByKeys = (collection, keys) =>
  _.filter(collection, (item) => !_.contains(keys, item.key));
const EXPERIMENT_COLUMN_KEYS = ["experiment"];
const REMOVED_COLUMNS_KEYS = [
  "favorite",
  "logs.stdout.content",
  "logs.stderr.content",
  "source_code.content",
  "observation",
  "suggestion",
  "optimized_suggestion",
];
const CHECKPOINT_COLUMN_KEYS = ["checkpoint_count"];

const filterOutUneededColumns = (
  definedFields,
  hasCheckpoints,
  hasExperiments,
) => {
  let columns = removeByKeys(definedFields, REMOVED_COLUMNS_KEYS);
  if (!hasCheckpoints) {
    columns = removeByKeys(columns, CHECKPOINT_COLUMN_KEYS);
  }
  if (!hasExperiments) {
    columns = removeByKeys(columns, EXPERIMENT_COLUMN_KEYS);
  }
  return columns;
};

const DEFAULT_COLUMN_ORDER = [
  "id",
  "name",
  "tags",
  "model.type",
  "state",
  "updated",
  "user",
];
const defaultSortColumns = (columns) => {
  const sortedByName = _.sortBy(columns, ({key}) => key.toLowerCase());
  const sortedAssignmentsFirst = _.sortBy(sortedByName, ({key}) =>
    key.startsWith("assignments.") ? -1 : 1,
  );
  const sortedValuesFirst = _.sortBy(sortedAssignmentsFirst, ({key}) =>
    key.startsWith("values.") ? -1 : 1,
  );

  return _.sortBy(sortedValuesFirst, ({key}) => {
    const index = DEFAULT_COLUMN_ORDER.indexOf(key);
    return index === -1 ? DEFAULT_COLUMN_ORDER.length + 1 : index;
  });
};

const createCheckpointsColumn = (hasCheckpoints) => {
  const width = hasCheckpoints ? 160 : 120;
  return {
    field: "checkpoint",
    headerName: "",
    maxWidth: width,
    pinned: "left",
    lockPinned: true,
    lockPosition: true,
    lockVisible: true,
    valueGetter: (params) => params.data.id,
    cellRenderer: CellRendererNames.CheckpointsCell,
    hide: !hasCheckpoints,
  };
};

const createCheckBoxAndExpandColumn = (hasCheckpoints) => {
  let cellRendererStuff = {cellRenderer: CellRendererNames.FavoriteCell};
  if (hasCheckpoints) {
    cellRendererStuff = {
      cellRenderer: "agGroupCellRenderer",
      cellRendererParams: {
        innerRenderer: CellRendererNames.FavoriteCell,
      },
    };
  }

  const width = hasCheckpoints ? 160 : 120;

  const checkBoxAndExpandColumn = {
    checkboxSelection: true,
    field: "favorite",
    filter: CUSTOM_FILTER_TYPES.SetFilter,
    headerCheckboxSelection: true,
    headerCheckboxSelectionFilteredOnly: true,
    headerClass: "favorite-hide-header",
    headerName: "Favorite",
    lockPinned: true,
    lockPosition: true,
    lockVisible: true,
    maxWidth: width,
    pinned: "left",
    resizable: false,
    suppressSizeToFit: true,
    valueGetter: (params) => params.data.favorite,
    width,
  };

  return _.extend(
    {},
    defaultColumnSettings,
    checkBoxAndExpandColumn,
    cellRendererStuff,
  );
};

const filterBySigColumnType = {
  id: AG_FILTER_TYPES.NUMERIC,
  string: AG_FILTER_TYPES.STRING,
  numeric: AG_FILTER_TYPES.NUMERIC,
  boolean: CUSTOM_FILTER_TYPES.SetFilter,
  timestamp: AG_FILTER_TYPES.DATE,
};

const agFilterColumnByKey = {
  state: CUSTOM_FILTER_TYPES.SetFilter,
  "model.type": CUSTOM_FILTER_TYPES.SetFilter,
};

const MAX_UNIQUE_FOR_SET = 10;
const createColumnOverridesForUnknownType = (runs, key) => {
  let isNumeric = true;
  let useSetFilter = true;
  const uniqueValues = [];
  for (let i = 0; i < runs.length; i += 1) {
    const run = runs[i];
    const value = lodashGet(run, key);
    if (isNumeric && isDefinedAndNotNull(value) && !_.isNumber(value)) {
      isNumeric = false;
    }
    if (useSetFilter && !_.contains(uniqueValues, value)) {
      uniqueValues.push(value);
    }
    if (uniqueValues.length > MAX_UNIQUE_FOR_SET) {
      useSetFilter = false;
    }
    if (!isNumeric && !useSetFilter) {
      break;
    }
  }

  if (isNumeric) {
    return {filter: AG_FILTER_TYPES.NUMERIC, type: AG_COLUMN_TYPES.NUMERIC};
  } else if (useSetFilter) {
    return {filter: CUSTOM_FILTER_TYPES.SetFilter};
  } else {
    return {filter: AG_FILTER_TYPES};
  }
};

const agColumnTypeBySigColumnType = {
  numeric: AG_COLUMN_TYPES.NUMERIC,
};

const columnOverridesByKey = {
  experiment: {
    cellRenderer: CellRendererNames.ExperimentLink,
    valueGetter: (row) => Number(row.data.experiment),
    type: AG_COLUMN_TYPES.NUMERIC,
    filter: CUSTOM_FILTER_TYPES.SetFilter,
  },
  id: {
    minWidth: 110,
    valueGetter: (params) => parseInt(params.data.id, 10) || null,
    cellRenderer: CellRendererNames.RunLink,
    type: AG_COLUMN_TYPES.NUMERIC,
  },
  name: {cellRenderer: CellRendererNames.RunLink},
  user: {cellRenderer: CellRendererNames.CreatedByLink},
  state: {filter: CUSTOM_FILTER_TYPES.SetFilter},
  datasets: {
    filter: CUSTOM_FILTER_TYPES.SetFilter,
    cellRenderer: CellRendererNames.DatasetsCell,
    keyCreator: (data) => _.keys(data.value),
  },
  tags: {
    cellRenderer: CellRendererNames.TagsCell,
    filter: CUSTOM_FILTER_TYPES.TagFilter,
    filterParams: {
      cellRenderer: CellRendererNames.TagFilterCell,
      defaultToNothingSelected: true,
    },
  },
};

const COLUMNS_HIDDEN_BY_DEFAULT = ["source_code.hash"];

const sigColumnToAgColumn = (runs, column) => {
  const filter = coalesce(
    agFilterColumnByKey[column.key],
    filterBySigColumnType[column.type],
  );
  const hide = _.contains(COLUMNS_HIDDEN_BY_DEFAULT, column.key);
  const type = agColumnTypeBySigColumnType[column.type];

  let cellRenderer = CellRendererNames[column.type];
  let tooltipComponent = null;
  let tooltipField = null;
  if (column.key.startsWith("assignments.")) {
    cellRenderer = CellRendererNames.ParameterCell;
    tooltipComponent = CellRendererNames.ParameterCellTooltip;
    tooltipField = column.key;
  }

  let unkownTypeOverrides = {};
  if (column.type === "unknown") {
    unkownTypeOverrides = createColumnOverridesForUnknownType(runs, column.key);
  }

  const columnSpecificSettings = {
    cellRenderer,
    tooltipComponent,
    tooltipField,
    filter,
    hide,
    type,
    colId: column.key,
    field: column.key,
    headerName: column.name,
  };

  const finalOverrides = columnOverridesByKey[column.key];

  return _.extend(
    {},
    defaultColumnSettings,
    columnSpecificSettings,
    unkownTypeOverrides,
    finalOverrides,
  );
};

// TODO(SN-1050): Think about grouping datasets
const groupAgColumns = (columns) => {
  const groups = {
    metrics: {
      children: [],
      headerClass: "group-header line-after",
      headerName: "Metrics",
      matchPrefix: "values.",
    },
    parameters: {
      children: [],
      headerClass: "group-header line-after",
      headerName: "Parameters",
      matchPrefix: "assignments.",
    },
  };
  const grouped = _.map(columns, (c) => {
    const matchedGroup = _.find(groups, (g) => {
      if (c.field.startsWith(g.matchPrefix)) {
        g.children.push(c);
        return g;
      }
      return null;
    });
    return matchedGroup || c;
  });
  return _.uniq(grouped);
};

const extendDefinedFields = (runs, definedFields) => {
  const extended = definedFields.concat([]);
  const definedDatasetCount = _.chain(runs)
    .pluck("datasets")
    .filter((d) => _.size(d) > 0)
    .size()
    .value();
  if (definedDatasetCount > 0) {
    extended.push({
      count: definedDatasetCount,
      key: "datasets",
      name: "Datasets",
      object: "field",
      sortable: false,
      type: "set",
    });
  }
  const definedTagCount = _.chain(runs)
    .pluck("tags")
    .filter((t) => _.size(t) > 0)
    .size()
    .value();
  extended.push({
    count: definedTagCount,
    key: "tags",
    name: "Tags",
    object: "field",
    sortable: false,
    type: "set",
  });
  extended.push({
    count: _.size(runs),
    key: "duration",
    name: "Duration",
    object: "field",
    sortable: false,
    type: CellRendererNames.DurationCell,
  });
  return extended;
};

export const createRunsTableColumnDefs = (
  runs,
  definedFields,
  hasCheckpoints,
  hasExperiments,
  sortColumns,
) => {
  const extendedFields = extendDefinedFields(runs, definedFields);
  const filteredColumns = filterOutUneededColumns(
    extendedFields,
    hasCheckpoints,
    hasExperiments,
  );
  const sortedColumns = (sortColumns || _.identity)(
    defaultSortColumns(filteredColumns),
  );
  const agColumns = _.map(sortedColumns, sigColumnToAgColumn.bind(null, runs));
  const groupedAgColumns = groupAgColumns(agColumns);

  const checkBoxAndExpandColumn = createCheckBoxAndExpandColumn(hasCheckpoints);
  const checkpointColumn = createCheckpointsColumn(hasCheckpoints);
  return [checkpointColumn, checkBoxAndExpandColumn, ...groupedAgColumns];
};
