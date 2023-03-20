/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import setFromUrlMatch from "./match";

export default function setMatchedClient() {
  return setFromUrlMatch(
    (req, s, e) =>
      req.services.legacyApiClient.clientDetail(req.params.clientId, s, e),
    (req, client) => {
      req.matchedClient = client;
    },
  );
}
