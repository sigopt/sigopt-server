/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import pluralize from "pluralize";

export const LongLabel = function (props) {
  const label = props.experiment.tasks ? " Budget Consumed" : " Observations";
  const observationStr = pluralize("Observation", props.count, true);
  return (
    <div className="title-label">
      {`${props.budgetConsumed}/${props.budget}${label}`}
      <div className="observation-count-progress">
        {props.experiment.tasks ? `After ${observationStr}` : null}
      </div>
    </div>
  );
};

export const ShortLabel = function (props) {
  return (
    <div className="title-label">{`${props.budgetConsumed}/${props.budget}`}</div>
  );
};
