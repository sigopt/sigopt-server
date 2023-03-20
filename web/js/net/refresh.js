/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

// Reloads the page for the user.
//
// If you pass {pathOnly: true}, then the page will be
// refreshed without the query params (?x=y)
// or the hash (#section)
export default function refreshPage(options) {
  if (options && options.pathOnly) {
    window.location = window.location.pathname;
  } else {
    window.location.reload();
  }
}
