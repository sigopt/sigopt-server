/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Service from "../services/base";
import Url from "./url";

export default class Navigator extends Service {
  navigateTo(href) {
    this.navigateToAllowExternal(new Url(href).resource);
  }

  navigateInNewTab(href) {
    window.open(new Url(href).resource, "_blank");
  }

  navigateToAllowExternal(href) {
    window.location = href;
  }
}
