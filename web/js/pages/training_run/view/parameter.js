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
import {ComplexTable} from "./complex_table";

const ActiveMessage = () => (
  <p>
    Parameter values will be recorded while the run is active if{" "}
    <code>sigopt.get_parameter</code> is executed in your code.
  </p>
);

export const Content = ({trainingRun}) => {
  const sources = trainingRun.assignments_sources || {};
  const parametersMeta = trainingRun.assignments_meta;
  const parameters = trainingRun.assignments;

  const paramsBySource = _.reduce(
    _.pairs(parameters),
    (acc, [parameter, value]) => {
      const source =
        parametersMeta[parameter] && parametersMeta[parameter].source;
      if (source) {
        acc.paramsBySource[source] = _.extend(
          {[parameter]: value},
          acc.paramsBySource[source],
        );
      } else {
        acc.noSourceParams[parameter] = value;
      }
      return acc;
    },
    {noSourceParams: {}, paramsBySource: {}},
  );

  const groups = _.values(
    _.mapObject(paramsBySource.paramsBySource, (params, sourceName) => ({
      title: sourceName,
      items: params,
      defaultOpen: sources[sourceName] && sources[sourceName].default_show,
      sort: sources[sourceName] && sources[sourceName].sort,
    })),
  );

  const noSources = groups.length === 0;

  if (_.keys(paramsBySource.noSourceParams).length > 0) {
    groups.unshift({
      title: "Parameters Without A Source",
      items: paramsBySource.noSourceParams,
      defaultOpen: true,
      sort: 0,
    });
  }

  const sorted_groups = _.sortBy(groups, (group) => group.sort);

  if (noSources) {
    return (
      <TableContent
        headers={["Name", "Value"]}
        content={sortObject(trainingRun.assignments)}
        copyObject={trainingRun.assignments}
      />
    );
  } else {
    return <ComplexTable headers={["Name", "Value"]} groups={sorted_groups} />;
  }
};

const EmptyMessage = () => (
  <p>
    No parameter values were recorded for your run. To see parameter values in
    future runs, add the following function to your code:
    {""}
    <br />
    <code>sigopt.params.setdefault(example, value)</code> and reference the
    parameter as <code>sigopt.params.example</code>.
  </p>
);

export default (props) => (
  <RunPageSection
    ActiveMessage={ActiveMessage}
    Content={Content}
    EmptyMessage={EmptyMessage}
    empty={_.isEmpty(props.trainingRun.assignments)}
    title="Parameter Values"
    {...props}
  />
);
