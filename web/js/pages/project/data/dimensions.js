/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {get as lodashGet} from "lodash";

import {isDefinedAndNotNull} from "../../../utils";

export const DIMENSION_GROUP_TYPES = {
  PARAMETER: "PARAMETER",
  METRIC: "METRIC",
  OTHER: "OTHER",
  METADATA: "METADATA",
};

export const DIMENSION_VALUE_TYPES = {
  CATEGORICAL: "CATEGORICAL",
  STRING: "STRING",
  ID: "ID",
  NUMERIC: "NUMERIC",
  BOOLEAN: "BOOLEAN",
  TIMESTAMP: "TIMESTAMP",
};

// We assume things are numeric, then categorical and finally fall back to being strings.
const UNKNOWN_VALUE_TYPES = {
  ASSUMED_NUMERIC: "ASSUMED_NUMERIC",
  ASSUMED_CATEGORICAL: "ASSUMED_CATEGORICAL",
};

const DIMENSION_VALUE_TYPE_OVERRIDES = {
  experiment: UNKNOWN_VALUE_TYPES.ASSUMED_CATEGORICAL,
};

const createEmptyDimension = (key, displayName, valueType) => {
  const dimGroupTest = key.split(".")[0];
  let groupType = DIMENSION_GROUP_TYPES.OTHER;
  if (dimGroupTest === "assignments") {
    groupType = DIMENSION_GROUP_TYPES.PARAMETER;
  } else if (dimGroupTest === "values") {
    groupType = DIMENSION_GROUP_TYPES.METRIC;
  } else if (dimGroupTest === "metadata") {
    groupType = DIMENSION_GROUP_TYPES.METADATA;
  }

  return {
    displayName,
    label: displayName,
    key,
    valueType,
    groupType,
    values: [],
    count: 0,
  };
};

const getValueTypeFromField = (field) => {
  let valueType = DIMENSION_VALUE_TYPES[field.type.toUpperCase()];
  if (valueType === DIMENSION_VALUE_TYPES.STRING) {
    valueType = UNKNOWN_VALUE_TYPES.ASSUMED_CATEGORICAL;
  }
  if (valueType === undefined) {
    valueType = UNKNOWN_VALUE_TYPES.ASSUMED_NUMERIC;
  }
  if (DIMENSION_VALUE_TYPE_OVERRIDES[field.key]) {
    valueType = DIMENSION_VALUE_TYPE_OVERRIDES[field.key];
  }

  return valueType;
};

const createEmptyDimensionsFromDefinedFields = (definedFields) =>
  _.map(definedFields, (field) => {
    const valueType = getValueTypeFromField(field);
    return createEmptyDimension(field.key, field.name, valueType);
  });

const fillDimensions = (emptyDimensions, runs) => {
  const idIndexMap = {};
  _.each(runs, (run, index) => {
    idIndexMap[run.id] = index;
    _.each(emptyDimensions, (dimension) => {
      const value = lodashGet(run, dimension.key);
      if (value !== null && value !== undefined) {
        dimension.count += 1;
      }
      dimension.values.push(value);
    });
  });

  return {filledDimensions: emptyDimensions, idIndexMap};
};

const handleAssumedNumeric = (dimensions, runs) => {
  const [assumedNumericDimensions, rest] = _.partition(
    dimensions,
    (d) => d.valueType === UNKNOWN_VALUE_TYPES.ASSUMED_NUMERIC,
  );

  _.each(runs, (run) => {
    _.each(assumedNumericDimensions, (dimension) => {
      const value = lodashGet(run, dimension.key);
      if (!_.isNumber(value) && isDefinedAndNotNull(value)) {
        dimension.valueType = UNKNOWN_VALUE_TYPES.ASSUMED_CATEGORICAL;
        dimension.categoricalValues = [];
      }
    });
  });

  return [...assumedNumericDimensions, ...rest];
};

// Becomes string when more than X categories
const MAX_CATEGORICAL_VALUES = 20;
const handleAssumedCategorical = (dimensions, runs) => {
  const [assumedCategoricalDimensions, rest] = _.partition(
    dimensions,
    (d) => d.valueType === UNKNOWN_VALUE_TYPES.ASSUMED_CATEGORICAL,
  );
  const categoricalOrStringDims = _.each(
    assumedCategoricalDimensions,
    (d) => (d.categoricalValues = []),
  );

  _.each(runs, (run) => {
    _.each(assumedCategoricalDimensions, (dimension) => {
      const value = lodashGet(run, dimension.key);
      if (
        dimension.valueType === UNKNOWN_VALUE_TYPES.ASSUMED_CATEGORICAL &&
        !_.contains(dimension.categoricalValues, value)
      ) {
        dimension.categoricalValues.push(value);
      }

      if (
        dimension.categoricalValues &&
        dimension.categoricalValues.length > MAX_CATEGORICAL_VALUES
      ) {
        dimension.valueType = DIMENSION_VALUE_TYPES.STRING;
        delete dimension.categoricalValues;
      }
    });
  });

  return [...categoricalOrStringDims, ...rest];
};

const makeDimensionTypesConcrete = (dimensions) => {
  _.each(dimensions, (dimension) => {
    if (dimension.valueType === UNKNOWN_VALUE_TYPES.ASSUMED_NUMERIC) {
      dimension.valueType = DIMENSION_VALUE_TYPES.NUMERIC;
    }
    if (dimension.valueType === UNKNOWN_VALUE_TYPES.ASSUMED_CATEGORICAL) {
      dimension.valueType = DIMENSION_VALUE_TYPES.CATEGORICAL;
    }
  });

  return dimensions;
};

const sortDimCategoricalValues = (values) => {
  const [numbers, rest] = _.partition(values, (v) => !isNaN(v));
  const [strings, nulls] = _.partition(rest, isDefinedAndNotNull);
  const sortedNumbers = _.sortBy(numbers, Number);
  const sortedStrings = strings.sort().reverse();
  return [...nulls, ...sortedStrings, ...sortedNumbers];
};

// Needed for plotly
const fillTickVals = (dimensions) => {
  const [categoricalDimensions, rest] = _.partition(
    dimensions,
    (d) => d.valueType === DIMENSION_VALUE_TYPES.CATEGORICAL,
  );
  _.each(categoricalDimensions, (dim) => {
    dim.tickvals = _.map(
      new Array(dim.categoricalValues.length),
      (unused, i) => i,
    );

    const dimValues = sortDimCategoricalValues(dim.categoricalValues);
    dim.ticktext = _.map(dimValues, String);
    dim.plotlyValues = _.map(dim.values, (val) => dimValues.indexOf(val));
  });

  return [...categoricalDimensions, ...rest];
};

const REMOVED_COLUMNS_KEYS = [
  "favorite",
  "logs.stdout.content",
  "logs.stderr.content",
  "source_code.content",
];
const filterOutUnplottableDimensions = (dimensions) =>
  _.filter(
    dimensions,
    (dim) => !_.contains(REMOVED_COLUMNS_KEYS, dim.key) && dim.count > 0,
  );

export const createDimensionsFromRuns = (definedFields, runs) => {
  const emptyDimensions = createEmptyDimensionsFromDefinedFields(definedFields);

  const {filledDimensions, idIndexMap} = fillDimensions(emptyDimensions, runs);
  const validDimensions = filterOutUnplottableDimensions(filledDimensions);

  const dimensionsWithAssumedNumericRemoved = handleAssumedNumeric(
    validDimensions,
    runs,
  );
  const dimensionsWithCorrectAssumedTypes = handleAssumedCategorical(
    dimensionsWithAssumedNumericRemoved,
    runs,
  );
  const dimensionsWIthCorrectTypes = makeDimensionTypesConcrete(
    dimensionsWithCorrectAssumedTypes,
  );
  const dimensionsWithTickVals = fillTickVals(dimensionsWIthCorrectTypes);

  const indexIdMap = _.invert(idIndexMap);

  return {
    dimensions: _.indexBy(dimensionsWithTickVals, "key"),
    idIndexMap,
    indexIdMap,
  };
};
