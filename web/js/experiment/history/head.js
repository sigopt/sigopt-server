/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import Header from "../../table/header";
import ui from "../ui";
import {isDefinedAndNotNull} from "../../utils";

const HistoryTableHead = function (props) {
  const canSort = Boolean(props.onSort);
  const hideStdDev = props.hideStdDev || {};

  const SortableHeader = function (hprops) {
    const active = hprops.sortKey === props.sortKey;
    return (
      <Header
        active={active}
        className={hprops.className}
        onClick={props.onSort}
        sortAscending={!active || props.sortAscending}
        sortKey={hprops.sortKey}
        sortable={canSort}
        title={hprops.name}
      >
        {hprops.name}
      </Header>
    );
  };

  const firstMetric = _.clone(_.first(props.experiment.metrics) || {});
  const firstName = firstMetric.name;
  firstMetric.name = firstMetric.name || "Value";
  const metricHeaders =
    props.showMetrics &&
    _.filter(
      ui.hasMultipleMetrics(props.experiment)
        ? _.chain(ui.sortMetrics(props.experiment.metrics))
            .map((m) => [
              <SortableHeader
                key={`value-${m.name}`}
                name={m.name}
                sortKey={m.name ? `value-${m.name}` : "value"}
              />,
              !hideStdDev[m.name] && (
                <SortableHeader
                  key={`value_stddev-${m.name}`}
                  name={`${m.name} Std. Deviation`}
                  sortKey={m.name ? `value_stddev-${m.name}` : "value_stddev"}
                />
              ),
            ])
            .flatten()
            .value()
        : [
            <SortableHeader
              key="value"
              sortKey="value"
              name={firstMetric.name}
            />,
            !hideStdDev[firstName] && (
              <SortableHeader
                key="value_stddev"
                sortKey="value_stddev"
                name="Standard Deviation"
              >
                Std. Deviation
              </SortableHeader>
            ),
          ],
      isDefinedAndNotNull,
    );

  return (
    <thead>
      <tr className="column-headers">
        <SortableHeader className="created" sortKey="id" name="Created" />
        {metricHeaders}
        {_.map(props.conditionals, (c) => (
          <th key={c.name}>{c.name}</th>
        ))}
        {props.experiment.tasks ? (
          <SortableHeader className="task" sortKey="task" name="Task Cost" />
        ) : null}
        {_.map(props.parameters, (p) =>
          _.isEmpty(props.experiment.conditionals) ? (
            <SortableHeader
              key={p.name}
              sortKey={`parameter-${p.name}`}
              name={p.name}
            />
          ) : (
            <th key={p.name}>{p.name}</th>
          ),
        )}
      </tr>
    </thead>
  );
};

HistoryTableHead.defaultProps = {showMetrics: true};

export default HistoryTableHead;
