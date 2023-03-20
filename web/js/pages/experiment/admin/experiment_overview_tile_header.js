/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import MaybeLink from "../../../component/link";
import ui from "../../../experiment/ui";
import {Duration, RelativeTime} from "../../../render/format_times";
import {isDefinedAndNotNull} from "../../../utils";

const ExperimentOverviewTileHeader = function (props) {
  const experiment = props.experiment;
  return (
    <span className="header-titles">
      <MaybeLink href={ui.getExperimentUrl(experiment)}>
        <div className="experiment-name">{experiment.name}</div>
      </MaybeLink>
      {isDefinedAndNotNull(experiment.progress.last_observation) && (
        <div className="experiment-runtime">
          Ran for{" "}
          <Duration
            startTime={experiment.progress.first_observation.created}
            endTime={experiment.progress.last_observation.created}
          />
        </div>
      )}
      {!isDefinedAndNotNull(experiment.progress.last_observation) && (
        <div className="experiment-runtime">Experiment has not started</div>
      )}
      <div className="experiment-created">
        Created {<RelativeTime time={experiment.created} />}
      </div>
    </span>
  );
};

export default ExperimentOverviewTileHeader;
