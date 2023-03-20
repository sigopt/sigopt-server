/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

const ProgressBar = function (props) {
  return (
    <div className="progress">
      <div
        className="progress-bar"
        role="progressbar"
        style={{width: `${100 * props.width}%`}}
      >
        {props.children}
      </div>
    </div>
  );
};

export default ProgressBar;
