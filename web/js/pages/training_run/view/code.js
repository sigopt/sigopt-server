/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import RunPageSection from "./section";
import {CodeBlock} from "../../../component/code_block";

const Content = ({trainingRun}) => {
  const sourceCode = trainingRun.source_code;
  return (
    <>
      {sourceCode.hash ? (
        <dl>
          <dt>Git Hash</dt>
          <dd>
            <code>{sourceCode.hash}</code>
          </dd>
        </dl>
      ) : null}
      {sourceCode.content ? (
        <CodeBlock language="python">{sourceCode.content}</CodeBlock>
      ) : (
        <EmptyMessage />
      )}
    </>
  );
};

const EmptyMessage = () => (
  <p>
    No source code is available for this run. To enable source code tracking for
    future runs, run <code>sigopt config</code> in your terminal.
  </p>
);

export default (props) => (
  <RunPageSection
    Content={Content}
    EmptyMessage={EmptyMessage}
    empty={_.isEmpty(props.trainingRun.source_code)}
    fullWidth={true}
    title="Code"
    {...props}
  />
);
