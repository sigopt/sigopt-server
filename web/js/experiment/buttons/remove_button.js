/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import XmarkGlyph from "../../component/glyph/xmark";

export const RemoveRowButton = function (props) {
  return (
    <a
      tabIndex="-1"
      onClick={props.removeRow}
      className="btn btn-xs btn-remove remove-parameter-button"
    >
      <XmarkGlyph glyph="xmark" />
    </a>
  );
};
RemoveRowButton.propTypes = {
  removeRow: PropTypes.func.isRequired,
};
