/**
 * Copyright © 2023 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {ClientSideRowModelModule} from "@ag-grid-community/client-side-row-model";
import {CsvExportModule} from "@ag-grid-community/csv-export";
import {InfiniteRowModelModule} from "@ag-grid-community/infinite-row-model";

export const allModules = [
  ClientSideRowModelModule,
  CsvExportModule,
  InfiniteRowModelModule,
];
