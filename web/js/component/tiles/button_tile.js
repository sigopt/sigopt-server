/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import BaseTile from "./base_tile";
import {TextButton} from "../buttons";

const ButtonTile = function (props) {
  return (
    <BaseTile {..._.omit(props, "info")}>
      <TextButton text={props.info.buttonText} onClick={props.info.onClick} />
    </BaseTile>
  );
};

ButtonTile.defaultProps = {tileClass: "button-tile"};
export default ButtonTile;
