/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import popLoginState from "../../session/pop";

const fetchUserInfo = (promiseApiClient, userId) =>
  Promise.all([
    promiseApiClient.users(userId).fetch(),
    promiseApiClient.users(userId).permissions().exhaustivelyPage(),
    promiseApiClient.users(userId).memberships().exhaustivelyPage(),
  ]);

const isForbidden = (err) => err && _.contains([401, 403, 404], err.status);

const getUserInfoEvenIfSessionExpired = (req) =>
  fetchUserInfo(req.services.promiseApiClient, req.loginState.userId).catch(
    (err) => {
      if (isForbidden(err) && req.loginState.parentState) {
        popLoginState(req);
        return getUserInfoEvenIfSessionExpired(req);
      } else {
        return Promise.reject(err);
      }
    },
  );

export default function setCurrentUser() {
  return (req, res, next) => {
    // TODO: What's a better way to restrict paths from checking
    // if the user is logged in?
    if (req.loginState.userId && !req.path.startsWith("/static/")) {
      getUserInfoEvenIfSessionExpired(req)
        .catch((err) => {
          if (isForbidden(err)) {
            req.loginState.setFrom(req.loginState.loggedOutCopy());
            return Promise.resolve([null, null, null]);
          } else {
            return Promise.reject(err);
          }
        })
        .then(([user, permissions, memberships]) => {
          req.currentUser = user;
          req.currentUserPermissions = permissions;
          req.currentUserMemberships = memberships;
        })
        .then(
          () => next(),
          (err) => next(err),
        );
    } else {
      req.currentUser = null;
      next();
      return;
    }
  };
}
