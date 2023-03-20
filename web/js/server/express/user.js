/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import setFromUrlMatch from "./match";

export default function setMatchedUser() {
  return setFromUrlMatch(
    (req, s, e) =>
      req.services.legacyApiClient.userDetail(req.params.userId, s, e),
    (req, user) => {
      req.matchedUser = user;
    },
  );
}
