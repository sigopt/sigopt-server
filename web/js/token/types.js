/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

export const TokenTypes = {
  DEVELOPMENT: "Development",
  API: "API",
  USER: "User",
  ROOT: "Root",
  GUEST: "Guest",
};

export const TokenScopes = {
  ALL_ENDPOINTS: "all_endpoints",
  SHARED_EXPERIMENT: "shared_experiment",
  SIGNUP: "signup",
};

export const getType = function (token) {
  if (token.development) {
    return TokenTypes.DEVELOPMENT;
  } else if (token.all_experiments && token.user && token.client) {
    return TokenTypes.API;
  } else if (token.all_experiments && token.user) {
    return TokenTypes.USER;
  } else if (token.all_experiments) {
    return TokenTypes.ROOT;
  } else {
    return TokenTypes.GUEST;
  }
};
