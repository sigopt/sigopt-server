/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./get_started.less";

import React from "react";

import {DOCS_URL} from "../net/constant";
import {OptimizationExample} from "../pages/home/components/welcome";

const GetStarted = () => (
  <>
    <p>
      Ready to kick off a project with a run? You can create runs from the
      command line, or within an IPython or Jupyter notebook.
    </p>
    <OptimizationExample />
    <p>
      Please refer to the{" "}
      <a href={`${DOCS_URL}/ai-module-api-references/tutorial`}>
        documentation
      </a>{" "}
      for more information.
    </p>
  </>
);

export default GetStarted;
