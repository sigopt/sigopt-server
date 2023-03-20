/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {coalesce} from "../../utils";

/**
 * Adds an `app.always`, which Specifies that a (req, res, next) handler should
 * always run, whether or not there is an error. If the error handler runs into
 * another error, the original error is silenced and replaced with the new
 * error.
 */
export default function addAlways(app) {
  app.always = (handler) => {
    app.use((err, req, res, next) => {
      const ourNext = (arg) => {
        const nextErr = coalesce(arg, err);
        // If there are two errors, we can only propogate one, so log the other
        if (err !== nextErr) {
          console.error(err); // eslint-disable-line no-console
        }
        next(nextErr);
      };
      handler(req, res, ourNext);
    });
    app.use((req, res, next) => handler(req, res, next));
  };
}
