/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import BaseTile from "./base_tile";

const TextListTile = function (props) {
  return (
    <BaseTile {..._.omit(props, "info")}>
      <ul>
        {_.map(props.info, (info) => (
          <li key={info}>{info}</li>
        ))}
      </ul>
    </BaseTile>
  );
};

TextListTile.defaultProps = {tileClass: "text-list-tile"};
export default TextListTile;
