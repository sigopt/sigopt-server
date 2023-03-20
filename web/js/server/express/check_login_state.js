/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {PRODUCT_NAME} from "../../brand/constant";

export default () => (req, res, next) => {
  const isValidClientId =
    req.loginState.clientId &&
    _.any(
      req.currentUserPermissions,
      (p) => p.client.id === req.loginState.clientId,
    );

  if (isValidClientId) {
    req.error = null;
    next();
    return;
  } else if (_.size(req.currentUserPermissions) > 0) {
    const organizationId = req.loginState.organizationId;
    // NOTE: default to permission in the same organization
    const permission =
      (organizationId &&
        _.find(
          req.currentUserPermissions,
          (p) => p.client.organization === organizationId,
        )) ||
      _.first(req.currentUserPermissions);
    const client = permission.client;
    if (req.loginState.clientId) {
      const errorMessage =
        "You have been removed from your team or it was deleted.";
      req.error = `${errorMessage} You are now acting on the ${client.name} team.`;
    } else {
      req.error = null;
    }
    req.loginState.clientId = client.id;
    req.loginState.organizationId = client.organization;
    next();
    return;
  } else {
    req.loginState.clientId = null;
    req.loginState.organizationId = null;
    req.error =
      `You must be invited to a team in order to use ${PRODUCT_NAME}.` +
      ` Contact your organization administrator.`;
    next();
    return;
  }
};
