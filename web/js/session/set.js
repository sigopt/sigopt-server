/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import LoginState from "./login_state";

const pushParentState = (
  loginState,
  preserveAsParentState,
  currentStateIsGuest,
) => {
  // Don't bother saving the parent state if it's not logged in
  // This is relevant when visiting a guest URL logged out, otherwise you see
  // the "End Session" banner and it's not very useful since clicking it just
  // logs you out
  const currentStateIsLoggedIn = Boolean(loginState.apiToken);
  // If the user is logged in as a guest, this is also not worth preserving and
  // should just be replaced with the new guest session. This is to prevent
  // infinite stacking of guest sessions
  if (preserveAsParentState && currentStateIsLoggedIn && !currentStateIsGuest) {
    loginState.parentState = new LoginState(loginState);
  } else {
    loginState.parentState ||= null;
  }
};

export const setLoginStateFromSession = (
  loginState,
  session,
  {preserveAsParentState = false} = {},
) => {
  pushParentState(loginState, preserveAsParentState, false);
  loginState.apiToken = session.api_token.token;
  loginState.clientId = session.client && session.client.id;
  loginState.organizationId = session.client && session.client.organization;
  loginState.userId = session.user && session.user.id;
};

export const setLoginStateFromToken = (
  loginState,
  newApiToken,
  currentApiToken,
  {preserveAsParentState = false} = {},
) => {
  const isGuest = currentApiToken && currentApiToken.token_type === "guest";
  pushParentState(loginState, preserveAsParentState, isGuest);
  loginState.apiToken = newApiToken.token;
  loginState.clientId = newApiToken.client;
  loginState.organizationId = newApiToken.organization;
  loginState.userId = newApiToken.user;
};
