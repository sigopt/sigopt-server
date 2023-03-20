/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

const VisibleBoolean = function (props) {
  return props.children ? <span>True</span> : <span>False</span>;
};
VisibleBoolean.propTypes = {
  children: PropTypes.bool.isRequired,
};

export default VisibleBoolean;
