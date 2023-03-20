/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/**
 * Pages through API requests until there are not more pages to fetch.
 *
 * fetcher is a function that takes 3 parameters.
 *   The first is a paging block, which can be of the form {limit: X, before: Y, after: Z}.
 *   The second is success, the third is error.
 */
import _ from "underscore";

import {isDefinedAndNotNull} from "../utils";

class PagerMonitor {
  constructor() {
    this.cancelled = false;
  }

  cancel() {
    this.cancelled = true;
  }
}

class StreamingPager {
  constructor(fetcher, onNewPage, onFinish, onError, params = undefined) {
    this._fetcher = fetcher;
    this._onNewPage = onNewPage;
    this._onFinish = onFinish;
    this._onError = onError;
    this._params = params;
    this.monitor = new PagerMonitor();
  }

  onNewPage(response) {
    if (this.monitor.cancelled) {
      return false;
    } else if (this._onNewPage) {
      this._onNewPage(response);
    }
    return true;
  }

  fetchNextPage(before) {
    return this._fetcher(_.extend({limit: 100, before: before}, this._params))
      .then((response) => {
        if (this.onNewPage(response)) {
          const newBefore = response.paging.before;
          if (isDefinedAndNotNull(newBefore)) {
            return this.fetchNextPage(newBefore);
          }
        }
        return Promise.resolve();
      })
      .catch((err) => {
        if (this.monitor.cancelled) {
          return Promise.resolve();
        } else {
          return Promise.reject(err);
        }
      });
  }

  start() {
    return this.fetchNextPage().then((result) => {
      if (!this.monitor.cancelled && this._onFinish) {
        this._onFinish(result);
      }
      return result;
    }, this._onError);
  }

  stop() {
    this.monitor.cancel();
  }
}

export default StreamingPager;
