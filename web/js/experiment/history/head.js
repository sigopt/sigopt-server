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

const SortableHeader = function (props) {
  return (
    <Header
      active={props.active}
      className={props.className}
      onClick={props.onSort}
      sortAscending={!props.active || props.sortAscending}
      sortKey={props.sortKey}
      sortable={props.canSort}
      title={props.name}
    >
      {props.name}
    </Header>
  );
};

const HistoryTableHead = function (props) {
  const canSort = Boolean(props.onSort);
  const hideStdDev = props.hideStdDev || {};

  const firstMetric = _.clone(_.first(props.experiment.metrics) || {});
  const firstName = firstMetric.name;
  firstMetric.name ||= "Value";
  const metricHeaders =
    props.showMetrics &&
    _.filter(
      ui.hasMultipleMetrics(props.experiment)
        ? _.chain(ui.sortMetrics(props.experiment.metrics))
            .map((m) => [
              <SortableHeader
                {...props}
                canSort={canSort}
                key={`value-${m.name}`}
                name={m.name}
                active={
                  (m.name ? `value-${m.name}` : "value") === props.sortKey
                }
              />,
              !hideStdDev[m.name] && (
                <SortableHeader
                  {...props}
                  canSort={canSort}
                  key={`value_stddev-${m.name}`}
                  name={`${m.name} Std. Deviation`}
                  active={
                    (m.name ? `value_stddev-${m.name}` : "value_stddev") ===
                    props.sortKey
                  }
                />
              ),
            ])
            .flatten()
            .value()
        : [
            <SortableHeader
              {...props}
              canSort={canSort}
              key="value"
              active={props.sortKey === "value"}
              name={firstMetric.name}
            />,
            !hideStdDev[firstName] && (
              <SortableHeader
                {...props}
                canSort={canSort}
                key="value_stddev"
                active={props.sortKey === "value_stddev"}
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
