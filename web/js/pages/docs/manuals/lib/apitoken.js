/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

export default (props) =>
  props.apiToken ? (
    <p>
      Your SigOpt API token is <code>{props.apiToken}</code>
    </p>
  ) : (
    <p>
      Find your SigOpt API token on the{" "}
      <a href="/tokens/info" target="_blank" rel="noopener noferrer">
        API tokens page
      </a>
      {""}.
    </p>
  );
