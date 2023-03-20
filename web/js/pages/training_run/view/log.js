/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import RunPageSection from "./section";
import {ClickableTabs, Tab} from "../../../component/tabs";
import {CopyableText} from "../../../component/code_block";

const ActiveMessage = () => (
  <p>
    This run is active, logs will be available when the run has completed if log
    collection was enabled. Log collection can be enabled by running{" "}
    <code>sigopt config</code> in the terminal.
  </p>
);

const LogContent = ({log, type}) => {
  if (_.isEmpty(log.content)) {
    return (
      <div className="alert alert-warning">
        Logs for {type} were captured, but there was no content.
      </div>
    );
  }
  return <CopyableText>{log.content}</CopyableText>;
};

const Content = ({trainingRun}) => {
  const {logs} = trainingRun;
  const sections = _.chain(logs)
    .pairs()
    .sortBy(([type]) => -Number(type === "stdout"))
    .map(([type, log]) => (
      <Tab key={type} label={type}>
        <LogContent log={log} type={type} />
      </Tab>
    ))
    .value();
  return _.size(sections) <= 1 ? (
    sections
  ) : (
    <ClickableTabs>{sections}</ClickableTabs>
  );
};

const Disclaimer = () =>
  "The maximum size of stored logs is 1KB. If your logs exceed this limit then they will be truncated.";

const EmptyMessage = () => (
  <p>
    No log output was captured for this run. To enable log collection for future
    runs, run <code>sigopt config</code> in your terminal.
  </p>
);

export default (props) => (
  <RunPageSection
    ActiveMessage={ActiveMessage}
    Content={Content}
    Disclaimer={Disclaimer}
    EmptyMessage={EmptyMessage}
    empty={_.isEmpty(props.trainingRun.logs)}
    fullWidth={true}
    title="Logs"
    {...props}
  />
);
