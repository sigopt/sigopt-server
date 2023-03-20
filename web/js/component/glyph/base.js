/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./base.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

// For a glyph type to be supported, it must be a valid FontAwesome icon, and it must be manually
// added to glyphs.less
// For all available glyphs, see http://fontawesome.io/icons/
const Glyph = (props) => {
  const weightClass =
    {
      regular: "far",
      solid: "fas",
    }[props.weight] || "fas";
  const className = classNames(
    `fa-${props.glyph}`,
    weightClass,
    props.className,
  );
  const ret = (
    <span
      {..._.omit(props, "className", "glyph", "fallback")}
      aria-hidden="true"
      aria-label={props.fallback}
      className={className}
    />
  );
  if (props.fallback) {
    return (
      <span>
        {ret}
        <span className="fa-fallback" aria-hidden="true">
          {props.fallback}
        </span>
      </span>
    );
  } else {
    return ret;
  }
};

Glyph.propTypes = {
  className: PropTypes.string,
  fallback: PropTypes.string,
  glyph: PropTypes.string.isRequired,
  weight: PropTypes.oneOf(["regular", "solid"]),
};

export default Glyph;
