/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const validateEmail = (email) =>
  // An actual regex for email would be enormous
  // and is not recommended. The least & most we can do
  // is check for the @ symbol.
  email && email.match(/.+@.+\..+/u);

export const extractDomainFromEmail = (email) =>
  email.substr(email.lastIndexOf("@") + 1);

export const extractLocalPartFromEmail = (email) => {
  return email.substr(0, email.indexOf("@"));
};

export const concatenateLocalPartAndDomain = (localPart, domain) =>
  `${localPart}@${domain}`;
