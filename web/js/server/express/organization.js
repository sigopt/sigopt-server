/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Redirect from "../../net/redirect";
import setFromUrlMatch from "./match";
import {NotFoundError} from "../../net/errors";

export default function setMatchedOrganization() {
  return setFromUrlMatch(
    (req, s, e) => {
      if (
        _.contains(
          ["experiments", "teams", "users", "runs"],
          req.params.organizationId,
        )
      ) {
        if (req.loginState.organizationId) {
          throw new Redirect(
            `/organization/${req.loginState.organizationId}/${req.params.organizationId}`,
          );
        } else {
          throw new NotFoundError();
        }
      } else {
        return req.services.legacyApiClient.organizationDetail(
          req.params.organizationId,
          s,
          e,
        );
      }
    },
    (req, organization) => {
      req.matchedOrganization = organization;
    },
  );
}
