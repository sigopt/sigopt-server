/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {AxisTypes} from "./constants";

const SUPPORTED_AXIS_TYPES = _.chain([
  AxisTypes.CONDITIONAL,
  AxisTypes.METADATA,
  AxisTypes.PARAMETER,
  AxisTypes.TASK,
  AxisTypes.OPTIMIZED_METRIC,
  AxisTypes.CONSTRAINED_METRIC,
  AxisTypes.STORED_METRIC,
])
  .map((type) => [type, true])
  .object()
  .value();

const findValueObject = ({value, value_stddev, values}, metricKey) => {
  const valueObject = _.isNumber(metricKey)
    ? values[metricKey]
    : _.find(values, ({name}) => name === metricKey);
  return valueObject || {value, value_stddev};
};

const assignmentGetter = ({assignments}, key) => (assignments || {})[key];
const metadataGetter = ({metadata}, key) => (metadata || {})[key];
export const metricValueGetter = (o, key) => findValueObject(o, key).value;
const metricValueStddevGetter = (o, key) =>
  findValueObject(o, key).value_stddev;
const taskGetter = ({task}) => (task || {}).name;

const valueGetters = {
  [AxisTypes.CONDITIONAL]: assignmentGetter,
  [AxisTypes.METADATA]: metadataGetter,
  [AxisTypes.PARAMETER]: assignmentGetter,
  [AxisTypes.TASK]: taskGetter,
  [AxisTypes.OPTIMIZED_METRIC]: metricValueGetter,
  [AxisTypes.CONSTRAINED_METRIC]: metricValueGetter,
  [AxisTypes.STORED_METRIC]: metricValueGetter,
};

const valueStddevGetters = {
  [AxisTypes.OPTIMIZED_METRIC]: metricValueStddevGetter,
  [AxisTypes.CONSTRAINED_METRIC]: metricValueStddevGetter,
  [AxisTypes.STORED_METRIC]: metricValueStddevGetter,
};

const makeAxisGetter =
  (getterMap) =>
  ({key, type}) => {
    if (SUPPORTED_AXIS_TYPES[type]) {
      const getter = getterMap[type] || _.noop;
      return (o) => getter(o, key);
    }
    throw new Error(`Unsupported axis type: ${type}`);
  };

export const axisValueGetter = makeAxisGetter(valueGetters);

export const axisValueStddevGetter = makeAxisGetter(valueStddevGetters);
