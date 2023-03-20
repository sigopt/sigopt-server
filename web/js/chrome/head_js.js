/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

// This exists to run JS before any of our bundles are downloaded/initialized

// NOTE: You can't reference outside code in this. (Hence the constants being returned from this)
const headCode = (getConstants) => {
  /* eslint-disable-next-line no-var */
  var constants = {INIT_CSP_ERROR_LOCATION: "_SIGOPT_INTERNAL_CSP_ERRORS"};
  if (getConstants) return constants;

  window[constants.INIT_CSP_ERROR_LOCATION] = [];
  window.addEventListener("securitypolicyviolation", (event) => {
    window[constants.INIT_CSP_ERROR_LOCATION].push(event);
  });

  return constants;
};

export const {INIT_CSP_ERROR_LOCATION} = headCode(true);

const funcString = headCode.toString().replace(/(\r\n|\n|\r)/gmu, "");
const funcName = "_SIGOPT_INIT_CODE";
export const headCodeString = `var ${funcName} = ${funcString};${funcName}();`;
