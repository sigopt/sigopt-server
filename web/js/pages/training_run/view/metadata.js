/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import RunPageSection from "./section";
import TableContent from "./table";
import sortObject from "./sort_object";

const ActiveMessage = () => (
  <p>
    Metadata will be added while the run is active if{" "}
    <code>sigopt.log_metadata</code> is executed in your code.
  </p>
);

export const Content = ({trainingRun}) => (
  <TableContent
    headers={["Key", "Value"]}
    content={sortObject(trainingRun.metadata)}
  />
);

const EmptyMessage = () => (
  <p>
    No metadata was created for your run. Metadata can be used to store
    arbitrary key/value pairs. To add metadata to future runs, add the following
    function to your code:
    {""}
    <br />
    <code>sigopt.log_metadata(key, value)</code>
  </p>
);

export default (props) => (
  <RunPageSection
    ActiveMessage={ActiveMessage}
    Content={Content}
    EmptyMessage={EmptyMessage}
    empty={_.isEmpty(props.trainingRun.metadata)}
    title="Metadata"
    {...props}
  />
);
