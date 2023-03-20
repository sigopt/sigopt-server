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
import {isDefinedAndNotNull} from "../../../utils";

const ActiveMessage = () => (
  <p>
    Metrics will be reported while the run is active if{" "}
    <code>sigopt.log_metric</code> is executed in your code.
  </p>
);

export const Content = ({trainingRun}) => (
  <TableContent
    headers={["Name", "Value"]}
    content={_.map(sortObject(trainingRun.values), ([key, value]) => [
      key,
      <React.Fragment key="for-lint-only">
        {value.value}
        {isDefinedAndNotNull(value.value_stddev) && (
          <>&plusmn;{value.value_stddev}</>
        )}
      </React.Fragment>,
    ])}
  />
);

const EmptyMessage = () => (
  <p>
    No metrics were reported for your run. It is highly recommended to report
    metrics for your runs. To report metrics and see them on future runs, add
    the following function to your code:
    {""}
    <br />
    <code>sigopt.log_metric(name, value, stddev=None)</code>
  </p>
);

export default (props) => (
  <RunPageSection
    ActiveMessage={ActiveMessage}
    Content={Content}
    EmptyMessage={EmptyMessage}
    empty={_.isEmpty(props.trainingRun.values)}
    title="Metrics"
    {...props}
  />
);
