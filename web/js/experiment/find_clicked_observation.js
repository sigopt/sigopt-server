/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

export default function (data, observations) {
  const point = data.points[0];
  return _.find(
    observations,
    (o) => o.id === point.data.observation_ids[point.pointNumber],
  );
}
