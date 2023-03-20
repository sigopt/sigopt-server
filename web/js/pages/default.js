/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import $ from "jquery";

import page from "../page";
import renderToPage from "../react/render";

page(function (options) {
  const html = $(".page-content");
  renderToPage({__html: html.html()}, options.$el);
});
