/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Redirect from "../../net/redirect";

export const setRedirect = function () {
  return (req, res, next) => {
    next();
    return;
  };
};

export const handleRedirects = function () {
  return (err, req, res, next) => {
    if (err instanceof Redirect) {
      res.redirect(err.status, err.location);
      return;
    } else if (err && err.tokenStatus === "needs_email_verification") {
      res.redirect(302, "/user/info?needs_verify=1");
    } else {
      next(err);
      return;
    }
  };
};
