/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import ApiToken from "../apitoken";
import configureAIModule from "./configure_ai_module.txt";
import frankeTemplate1 from "../../../templates/franke_python_p1.ms";
import frankeTemplate2 from "../../../templates/franke_python_p2.ms";
import installPythonTemplate from "../../../templates/install_python.ms";
import renderedTemplate from "../renderedtemplate";
import {CodeBlock} from "../../../../../component/code_block";
import {DOCS_URL} from "../../../../../net/constant";

export const PythonInstallCodeSection = (props) => (
  <div>
    <p>You can use our Python Client to create and run AI Experiments.</p>
    <p>
      Our Python API Client is available via pip, with source code on{" "}
      <a href="https://github.com/sigopt/sigopt-python#sigopt-python-api">
        GitHub
      </a>
      {""}:
    </p>
    <CodeBlock language="bash">
      {renderedTemplate(installPythonTemplate, props)}
    </CodeBlock>
    <ApiToken apiToken={props.apiToken} />
    <CodeBlock language="bash">{configureAIModule}</CodeBlock>
  </div>
);

export const PythonCreateCodeSection = (props) => (
  <div>
    <p>
      The next step is to set up the AI Experiment. Here you can define your
      parameters, metrics and budget, among other things. Check out the full
      list of supported fields in our{" "}
      <a
        href={`${DOCS_URL}/ai-module-api-references/objects/object_experiment`}
      >
        documentation
      </a>
      {""}.
    </p>
    <CodeBlock language="python">
      {renderedTemplate(frankeTemplate1, props)}
    </CodeBlock>
  </div>
);

export const PythonOptimizeCodeSection = (props) => (
  <div>
    <p>
      Now, you can run SigOpt&apos;s{" "}
      <a href={`${DOCS_URL}/experiments/main-concepts#optimization-loop`}>
        Optimization Loop
      </a>
      {""}.
    </p>
    <CodeBlock language="python">
      {renderedTemplate(frankeTemplate2, props)}
    </CodeBlock>
  </div>
);
