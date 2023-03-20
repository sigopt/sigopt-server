/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./component.less";

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";
import luminance from "color-luminance";

import XmarkGlyph from "../component/glyph/xmark";
import {colorHexToRGB} from "../utils";

// NOTE: this threshold was chosen emperically.
// there is probably no optimal number since color perception can vary
const BLACK_TEXT_LUMINANCE_THRESHOLD = 0.7;

const getTextColor = (hexColor) => {
  const {r, g, b} = colorHexToRGB(hexColor);
  const perceivedLuminance = luminance.rec709(r, g, b);
  return perceivedLuminance > BLACK_TEXT_LUMINANCE_THRESHOLD * 0xff
    ? "#000000"
    : "#FFFFFF";
};

export default function Tag({data, removeProps, innerProps, innerRef}) {
  return (
    <div
      className={classNames("tag", {clickable: Boolean(innerProps)})}
      ref={innerRef}
      {...innerProps}
      style={{
        backgroundColor: data.color,
        color: getTextColor(data.color),
      }}
    >
      {data.name}
      {removeProps && (
        <span {...removeProps} className="remove-tag">
          <XmarkGlyph />
        </span>
      )}
    </div>
  );
}

Tag.propTypes = {
  data: PropTypes.shape({
    color: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
  }).isRequired,
  innerProps: PropTypes.object,
  innerRef: PropTypes.oneOfType([PropTypes.func, PropTypes.object]),
  removeProps: PropTypes.object,
};
