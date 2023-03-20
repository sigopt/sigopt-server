/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {configureStore, getDefaultMiddleware} from "@reduxjs/toolkit";

import {rootReducer} from "./root_reducer";

const customizedMiddleware = getDefaultMiddleware({
  serializableCheck: false,
  immutableCheck: false,
});

const actionSanitizer = (action) => ({...action, payload: null});

export const createDashBoardStore = (
  project,
  client,
  user,
  promiseApiClient,
) => {
  const store = configureStore({
    reducer: rootReducer,
    preloadedState: {
      resources: {project, client, user},
      services: {promiseApiClient},
    },
    middleware: customizedMiddleware,
    devTools: {
      actionsBlacklist: ["dimensions/setHoverInfo"],
      actionSanitizer,
      stateSanitizer: (state) => ({
        ...state,
        services: "NOT IN DEV TOOLS",
        "dimensions.tableApi": "NOT IN DEV TOOLS",
      }),
    },
  });

  if (process.env.NODE_ENV === "development" && module.hot) {
    module.hot.accept("./root_reducer", () => {
      const newRootReducer = require("./root_reducer").rootReducer;
      store.replaceReducer(newRootReducer);
    });
  }

  return store;
};
