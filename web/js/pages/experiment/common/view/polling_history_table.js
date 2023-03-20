/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import CSSTransition from "react-transition-group/CSSTransition";
import React from "react";
import TransitionGroup from "react-transition-group/TransitionGroup";

import HistoryTableHead from "../../../../experiment/history/head";
import HistoryTableRow from "../../../../experiment/history/row";
import byNaturalSortName from "../../../../experiment/sort_params";

const PollingHistoryTable = function (props) {
  const hideStdDev = _.chain(props.observations)
    .map((o) => o.values)
    .flatten()
    .groupBy("name")
    .mapObject((vs) => _.all(vs, (v) => _.isNull(v.value_stddev)))
    .value();
  const conditionals = _.clone(props.experiment.conditionals || []).sort(
    byNaturalSortName,
  );
  const parameters = _.clone(props.experiment.parameters || []).sort(
    byNaturalSortName,
  );
  return (
    <div className="table-responsive history-table">
      <table className="table table-hover">
        <HistoryTableHead
          canEdit={false}
          conditionals={conditionals}
          experiment={props.experiment}
          hideStdDev={hideStdDev}
          expectingMoreCheckpoints={false}
          parameters={parameters}
          showMetadata={false}
        />
        <TransitionGroup component="tbody">
          {_.map(props.observations, (observation) => (
            <CSSTransition
              classNames="history-animate"
              timeout={800}
              key={observation.id}
            >
              <HistoryTableRow
                {...props}
                assignments={observation.assignments}
                canEdit={false}
                conditionals={conditionals}
                created={observation.created}
                failed={observation.failed}
                hideStdDev={hideStdDev}
                onClick={() => props.onSelectObservation(observation)}
                parameters={parameters}
                resource={observation}
                showValues={true}
                values={observation.values}
                taskCost={observation.task && observation.task.cost}
              />
            </CSSTransition>
          ))}
        </TransitionGroup>
      </table>
    </div>
  );
};

export default PollingHistoryTable;
