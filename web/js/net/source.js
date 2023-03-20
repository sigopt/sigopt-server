/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

/**
 * Allows idempotent fetching of data.
 *
 * A DataSource indicates data that will be available in the future.
 * Call `getData` to register a success/error callbackst that will
 * be called when the data is available, or immediately if it is
 * available now.
 */

class DataSource {
  constructor() {
    this._hasData = false;
    this._didSucceed = null;
    this._responseArgs = null;
    this._successCallbacks = [];
    this._errorCallbacks = [];
    this._populateData = _.once(this._doPopulateData);
  }

  getData(successCallback, errorCallback) {
    if (this._hasData) {
      if (this._didSucceed) {
        if (successCallback) {
          successCallback(...this._responseArgs);
        }
      } else if (errorCallback) {
        errorCallback(...this._responseArgs);
      }
    } else {
      this._successCallbacks.push(successCallback);
      this._errorCallbacks.push(errorCallback);
      this._populateData();
    }
  }

  _doPopulateData() {
    this._fetchData(
      (...args) => {
        this._hasData = true;
        this._didSucceed = true;
        this._responseArgs = args;
        _.each(this._successCallbacks, (c) => c && c(...args));
      },
      (...args) => {
        this._hasData = true;
        this._didSucceed = false;
        this._responseArgs = args;
        _.each(this._errorCallbacks, (c) => c && c(...args));
      },
    );
  }

  // Implemented by subclasses
  // Takes a `success` and `error` callback.
  // _fetchData(success, error)
}

/**
 * A DataSource that uses the provided fetcher to
 * The available data will be the exhaustively paged list.
 */
export class AsynchronousDataSource extends DataSource {
  constructor(fetcher, errorNotifier) {
    super();
    this._fetcher = fetcher;
    this._errorNotifier = errorNotifier;
  }

  _fetchData(success, error) {
    this._fetcher(success, (...errorArgs) => {
      this._errorNotifier.cleanupError(errorArgs[0]);
      error(...errorArgs);
    });
  }
}

/**
 * A DataSource that is immediately available. Returns the provided value
 * immediately, and will never error or return asynchronously.
 */
export class AvailableDataSource extends DataSource {
  constructor(...args) {
    super();
    this._hasData = true;
    this._didSucceed = true;
    this._responseArgs = args;
  }
}
