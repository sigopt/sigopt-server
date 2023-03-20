/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {coalesce} from "../../utils";

export default function setCurrentOrganization() {
  return (req, res, next) => {
    if (req.currentUser) {
      if (req.loginState.organizationId) {
        req.services.promiseApiClient
          .organizations(req.loginState.organizationId)
          .fetch()
          .then(
            (organization) => {
              req.currentOrganization = organization;
              next();
            },
            (err) => {
              if (err && _.contains([404], err.status)) {
                req.currentOrganization = null;
                next();
                return;
              } else {
                next(err);
                return;
              }
            },
          );
        return;
      } else {
        req.services.promiseApiClient
          .users(req.currentUser.id)
          .memberships()
          .fetch({limit: 1})
          .then((pagination) => {
            const organization =
              pagination.data[0] && pagination.data[0].organization;
            req.currentOrganization = coalesce(organization, null);
            next();
            return;
          });
      }
    } else {
      req.currentOrganization = null;
      next();
      return;
    }
  };
}
