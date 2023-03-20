/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

// https://owasp.org/www-community/attacks/CSV_Injection
const invalidStartCharacters = ["=", "-", "+", "@"];

const LEADING_SPACES_REGEX = /^ */u;
const trimLeadingSpaces = (s) => s.replace(LEADING_SPACES_REGEX, "");
const addLeadingSpace = (s) => ` ${s}`;
const maybeRemoveLeadingSpace = (s) => (s.startsWith(" ") ? s.substring(1) : s);
const hasDangerousPrefix = (s) =>
  _.any(invalidStartCharacters, (c) => trimLeadingSpaces(s).startsWith(c));
const shouldSanitize = (s) => _.isString(s) && hasDangerousPrefix(s);

export const excelSanitize = (s) =>
  shouldSanitize(s) ? addLeadingSpace(s) : s;
export const excelUnsanitize = (s) =>
  shouldSanitize(s) ? maybeRemoveLeadingSpace(s) : s;
