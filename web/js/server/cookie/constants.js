/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const S3_SAFE_REGEX = /^[0-9a-z!-_.*'()]+$/iu;
export const SESSION_ID_LENGTH_BYTES = 64;
export const BASE64_ENCODED_SESSION_ID_LENGTH = 88;
export const BASE64_REPLACEMENTS = {
  "=": ".", // url-safe-base64 considers `=` to be url safe, but it is not a safe character for S3
};
export const DEFAULT_COOKIE_EXPIRY_SECONDS = 36 * 60 * 60;
