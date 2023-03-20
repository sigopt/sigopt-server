/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/project_runs_page_local.less";

import React from "react";

import ProjectPage from "../page_wrapper";
import {ProjectRunsTable} from "./project_run_table";

export default (props) => (
  <ProjectPage {...props}>
    <ProjectRunsTable {...props} />
  </ProjectPage>
);
