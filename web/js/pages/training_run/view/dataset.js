/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import RunPageSection from "./section";
import {naturalStringCompare} from "../../../utils";

const ActiveMessage = () => (
  <p>
    Dataset information will be recorded while the run is active if{" "}
    <code>sigopt.log_dataset</code> is executed in your code.
  </p>
);

const Content = ({trainingRun}) => (
  <ul>
    {_.chain(trainingRun.datasets)
      .keys()
      .sort(naturalStringCompare)
      .map((dataset) => <li key={dataset}>{dataset}</li>)
      .value()}
  </ul>
);

const EmptyMessage = () => (
  <p>
    No datasets were recorded for your run. To see your datasets with future
    runs, add the following function to your code:
    {""}
    <br />
    <code>sigopt.log_dataset(name)</code>
  </p>
);

export default (props) => (
  <RunPageSection
    ActiveMessage={ActiveMessage}
    Content={Content}
    EmptyMessage={EmptyMessage}
    empty={_.isEmpty(props.trainingRun.datasets)}
    title="Datasets"
    {...props}
  />
);
