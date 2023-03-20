/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const make2dScatterJson = (xDim, yDim, xNum, yNum) => {
  const hovertemplate = `${xDim.displayName}: %{x}<br />${yDim.displayName}: %{y}<extra></extra>`;

  const data = {
    type: "scatter",
    mode: "markers",
    hoverinfo: "skip",
    hovertemplate,
    marker: {
      size: 10,
    },
    x: xDim.values,
    y: yDim.values,
    xaxis: `x${xNum}`,
    yaxis: `y${yNum}`,
  };

  const layout = {
    [`xaxis${xNum}`]: {title: xDim.displayName},
    [`yaxis${yNum}`]: {title: yDim.displayName},
  };

  return {data, layout};
};
