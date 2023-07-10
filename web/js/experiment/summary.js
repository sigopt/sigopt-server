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
import classNames from "classnames";

import BestAssignmentsTable from "./best_assignments";
import CircleArrowRightGlyph from "../component/glyph/circle-arrow-right";
import Loading from "../component/loading";
import SatisfiesThresholdsLoading from "./best_assignments_loading";
import ui from "./ui";
import {AssignmentsTable} from "./model_evaluation";
import {coalesce, isDefinedAndNotNull, renderNumber} from "../utils";

export default function ExperimentSummary({
  bestAssignments,
  canEdit,
  experiment,
  observations,
  onSelectBestAssignment,
}) {
  const isSingleBest = ui.isExperimentSingleBest(experiment);
  const firstBest = _.first(bestAssignments);
  const bestValue = isDefinedAndNotNull(firstBest)
    ? ui.optimizedValues(experiment, firstBest.values)[0]
    : null;
  const hasBestValue = isDefinedAndNotNull(bestValue);
  return (
    <div className="improvement top-cell">
      <div
        className={classNames("summary-holder", "cell-content", {
          loading: !isDefinedAndNotNull(bestAssignments),
        })}
      >
        <Loading loading={!isDefinedAndNotNull(bestAssignments)}>
          <div className="summary-wrap">
            <div className="info-message">
              <span className="text">
                {_.isEmpty(bestAssignments)
                  ? "View history"
                  : "Show best observation"}
              </span>
              <CircleArrowRightGlyph />
            </div>
            <div className="experiment-summary scroll">
              {isSingleBest ? (
                <div className="value-section">
                  <div className="best-value">
                    <div className="improvement-label">Best Value</div>
                    <SatisfiesThresholdsLoading
                      canEdit={canEdit}
                      experiment={experiment}
                      observations={observations}
                    >
                      <div className="improvement-number">
                        {hasBestValue ? renderNumber(bestValue, true) : null}
                      </div>
                    </SatisfiesThresholdsLoading>
                  </div>
                </div>
              ) : null}
              {!hasBestValue && isDefinedAndNotNull(experiment.tasks) && (
                <div className="no-best">
                  <div className="no-best-message">
                    No full cost observations yet. Multitask experiments only
                    count full-cost Observations when calculating your Best
                    Observation. Please check back later or view your Experiment
                    History to see what Observations have been submitted.
                  </div>
                </div>
              )}
              {isSingleBest && firstBest ? (
                <AssignmentsTable
                  assignments={firstBest.assignments}
                  experiment={experiment}
                  onClick={
                    onSelectBestAssignment
                      ? () => onSelectBestAssignment(firstBest)
                      : null
                  }
                  scrollable={true}
                />
              ) : null}
              {!isSingleBest && (
                <div>
                  <div className="best-parameters-label">
                    Current Best Values
                  </div>
                  <SatisfiesThresholdsLoading
                    canEdit={canEdit}
                    experiment={experiment}
                    observations={observations}
                  >
                    <TransitionGroup>
                      {_.map(bestAssignments, (bestObservation) => (
                        <CSSTransition
                          classNames="improvement-animate"
                          key={
                            // NOTE: bestObservation.id is missing for multisolution experiments,
                            // TODO(SN-1159): Get to the bottom of this, but this fixes the page
                            coalesce(bestObservation.id, bestObservation.value)
                          }
                          timeout={800}
                        >
                          <BestAssignmentsTable
                            bestObservation={bestObservation}
                            experiment={experiment}
                            onClick={
                              onSelectBestAssignment
                                ? () => onSelectBestAssignment(bestObservation)
                                : null
                            }
                          />
                        </CSSTransition>
                      ))}
                    </TransitionGroup>
                  </SatisfiesThresholdsLoading>
                </div>
              )}
            </div>
          </div>
        </Loading>
      </div>
    </div>
  );
}
