/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import escapeForScriptTag from "./script";

export default (props) => (
  <script
    dangerouslySetInnerHTML={escapeForScriptTag(JSON.stringify(props.data))}
    id={props.id}
    style={{display: "none"}}
    type="application/json"
  />
);
