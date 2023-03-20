/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {StaleStateError} from "./errors";

export const getDimension = (dimensions, key, recoverable = true) => {
  const dimension = dimensions[key];
  if (dimension === undefined) {
    const cause = `The dimension: ${key} is no longer valid. Possibly due to a filter change`;
    throw new StaleStateError(recoverable, cause);
  }
  return dimension;
};

export const getDimensions = (dimensions, keys, recoverable = true) =>
  _.map(keys, (key) => getDimension(dimensions, key, recoverable));

export const getPossibleDimensions = (dimensions, keys, recoverable = true) => {
  const dims = [];
  const invalidDims = [];

  _.map(keys, (key) => {
    try {
      dims.push(getDimension(dimensions, key, recoverable));
    } catch (err) {
      invalidDims.push(key);
    }
  });

  return {dims, invalidDims};
};
