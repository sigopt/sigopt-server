/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

export default (props) => (
  <div
    className="modal-dialog"
    onMouseDown={(event) => event.stopPropagation()}
  >
    <div className="modal-content">{props.children}</div>
  </div>
);
