/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import BaseTile from "./base_tile";
import Chiclets from "../chiclets";

const ChicletInfoTile = function (props) {
  return (
    <BaseTile {..._.omit(props, "info")}>
      <Chiclets chiclets={props.info} />
    </BaseTile>
  );
};

ChicletInfoTile.defaultProps = {tileClass: "chiclet-info-tile"};
export default ChicletInfoTile;
