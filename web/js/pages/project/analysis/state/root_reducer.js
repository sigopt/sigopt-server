/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {combineReducers} from "@reduxjs/toolkit";

import {DashboardsReducer} from "./dashboards_slice";
import {DimenensionsReducer} from "../../state/dimensions_slice";
import {ResourcesReducer} from "../../state/resources_slice";
import {ServicesReducer} from "../../state/services_slice";
import {ViewsReducer} from "../../state/views_slice";

export const rootReducer = combineReducers({
  dashboards: DashboardsReducer,
  resources: ResourcesReducer,
  services: ServicesReducer,
  views: ViewsReducer,
  dimensions: DimenensionsReducer,
});
