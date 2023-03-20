/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {createSlice} from "@reduxjs/toolkit";

const initialServicesSlice = {
  promiseApiClient: null,
};

const servicesSlice = createSlice({
  name: "services",
  initialState: initialServicesSlice,
  reducers: {},
});

export const ServicesReducer = servicesSlice.reducer;
