/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import BaseTile from "./base_tile";

const ListInfoTile = function (props) {
  return (
    <BaseTile {..._.omit(props, "info")}>
      <ul>
        {_.map(props.info, ([info, subtitle]) => (
          <li key={subtitle}>
            <span className="data">{info}</span>{" "}
            <span className="source">{subtitle}</span>
          </li>
        ))}
      </ul>
    </BaseTile>
  );
};

ListInfoTile.defaultProps = {tileClass: "list-info-tile"};
export default ListInfoTile;
