/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {idKey} from "../utils";

export default function (observations, ascending = true) {
  // sort chronologically (by ID if it exists, otherwise by timestamp)
  if (_.isEmpty(observations)) {
    return observations;
  }

  let sorted = observations;
  if (observations[0].id) {
    sorted = _.sortBy(observations, idKey);
  } else if (observations[0].created) {
    sorted = _.sortBy(observations, (o) => o.created);
  }

  if (!ascending) {
    sorted.reverse();
  }

  return sorted;
}
