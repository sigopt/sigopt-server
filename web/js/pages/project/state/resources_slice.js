/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {createSlice} from "@reduxjs/toolkit";

const initialState = {
  project: null,
  user: null,
  client: null,
};

const resourcesSlice = createSlice({
  name: "resources",
  initialState,
  reducers: {},
});

export const ResourcesReducer = resourcesSlice.reducer;
