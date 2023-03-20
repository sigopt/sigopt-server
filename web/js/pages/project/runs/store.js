/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {
  combineReducers,
  configureStore,
  getDefaultMiddleware,
} from "@reduxjs/toolkit";

import {DimenensionsReducer} from "../state/dimensions_slice";
import {ResourcesReducer} from "../state/resources_slice";
import {ServicesReducer} from "../state/services_slice";
import {ViewsReducer} from "../state/views_slice";

export const rootReducer = combineReducers({
  resources: ResourcesReducer,
  services: ServicesReducer,
  views: ViewsReducer,
  dimensions: DimenensionsReducer,
});

const customizedMiddleware = getDefaultMiddleware({
  serializableCheck: false,
  immutableCheck: false,
});

export const createRunsStore = (project, client, user, promiseApiClient) => {
  return configureStore({
    reducer: rootReducer,
    preloadedState: {
      resources: {project, client, user},
      services: {promiseApiClient},
    },
    middleware: customizedMiddleware,
  });
};
