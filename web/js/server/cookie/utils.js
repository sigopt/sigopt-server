/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {encode as encodeUrlSafeBase64, isUrlSafeBase64} from "url-safe-base64";
import {randomBytes} from "crypto";

import {
  BASE64_ENCODED_SESSION_ID_LENGTH,
  BASE64_REPLACEMENTS,
  DEFAULT_COOKIE_EXPIRY_SECONDS,
  S3_SAFE_REGEX,
  SESSION_ID_LENGTH_BYTES,
} from "./constants";

export function cookieExpiryInSeconds(configBroker) {
  return configBroker.get(
    "login_session.idle_timeout_seconds",
    DEFAULT_COOKIE_EXPIRY_SECONDS,
  );
}

export function cookieExpiryInMillis(configBroker) {
  return cookieExpiryInSeconds(configBroker) * 1000;
}

export function newRandomCookieId() {
  const unsafeNewId = encodeUrlSafeBase64(
    randomBytes(SESSION_ID_LENGTH_BYTES).toString("base64"),
  );
  return _.map(unsafeNewId, (c) => BASE64_REPLACEMENTS[c] || c).join("");
}

function isS3Safe(cookieId) {
  return Boolean(cookieId.match(S3_SAFE_REGEX));
}

export function isValidCookieId(cookieId) {
  return (
    !_.isEmpty(cookieId) &&
    isUrlSafeBase64(cookieId) &&
    isS3Safe(cookieId) &&
    _.size(cookieId) === BASE64_ENCODED_SESSION_ID_LENGTH
  );
}
