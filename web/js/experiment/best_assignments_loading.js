/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Loading from "../component/loading";
import schemas from "../react/schemas";
import ui from "./ui";
import {isUndefinedOrNull} from "../utils";

export default function SatisfiesThresholdsLoading({
  canEdit,
  children,
  experiment,
  isMultitask,
  observations,
}) {
  return (
    <Loading
      empty={
        !isMultitask &&
        !ui.hasObservationsThatSatisfyThresholds(experiment, observations)
      }
      emptyMessage={
        <span className="no-best-values-info">
          <i>
            No observation(s) satisfy the thresholds yet.{" "}
            {canEdit ? (
              <>
                You can edit metric thresholds on the{" "}
                <a href={ui.getExperimentUrl(experiment, "/properties")}>
                  properties page
                </a>
                {""}.
              </>
            ) : null}
          </i>
        </span>
      }
      loading={isUndefinedOrNull(observations)}
    >
      {children}
    </Loading>
  );
}

SatisfiesThresholdsLoading.propTypes = {
  canEdit: PropTypes.bool,
  children: PropTypes.node,
  experiment: schemas.Experiment.isRequired,
  isMultitask: PropTypes.bool,
  observations: PropTypes.arrayOf(schemas.Observation),
};
