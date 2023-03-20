/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {AsynchronousDataSource, AvailableDataSource} from "../net/source";

export class AsynchronousUserDataSource extends AsynchronousDataSource {
  constructor(userId, options) {
    const customHandler = (userid, success, error) => {
      options.legacyApiClient.userDetail(userid, success, (...errorargs) => {
        // Unauthorized to view (handled manually)
        if (errorargs[0].jqXhr.status === 404) {
          // Pass a null object so the user object is set to null
          success(null);
          return false;
        } else {
          error(...errorargs);
          return true;
        }
      });
    };
    super(_.partial(customHandler, userId), options.errorNotifier);
    this.userId = userId;
  }
}

export class AvailableUserDataSource extends AvailableDataSource {
  constructor(userId, options) {
    super(options.currentUser);
  }
}
