/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Url from "./url";

export default function validateContinueHref(continueHref, configBroker) {
  if (!continueHref) {
    return continueHref;
  }

  const parsedUrl = new Url(continueHref);
  if (!parsedUrl.origin) {
    return continueHref;
  }

  const appUrl = configBroker.get("address.app_url");
  // NOTE: This check has some false negatives. For example,
  // https://sigopt.ninja and https://sigopt.ninja:443 will be treated
  // as different, even though those refer to the same host since the default
  // port for https is 443. However, since this is for security, we want to
  // be pretty careful here
  if (parsedUrl.origin === appUrl) {
    return continueHref;
  }

  // Forbid external
  return null;
}
