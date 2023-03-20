/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./new_client_banner.less";

import React from "react";

import {DOCS_URL} from "../net/constant";

export const NewClientBanner = () => (
  <div className="alert alert-new-client">
    <p>
      Try out the new and improved SigOpt experience. Visit{" "}
      <a href={DOCS_URL}>the docs</a> to see how you can get started.
      Happy&nbsp;modeling!
    </p>
  </div>
);
