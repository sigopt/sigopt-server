/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import renderToPage from "../react/render";
import waitForServices from "../page";

waitForServices((options) => {
  const PageComponent = window.PageComponent || React.Fragment;
  renderToPage(<PageComponent {...options} />, options.$el);
});
