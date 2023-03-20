/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

const Icon = function (props) {
  return (
    <div
      className="sigopt-icon"
      style={{backgroundImage: `url(${props.imgSrc})`}}
    />
  );
};
Icon.propTypes = {
  imgSrc: PropTypes.string.isRequired,
};

export default Icon;
