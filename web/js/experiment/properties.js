/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Tooltip from "../component/tooltip";
import TooltipInput from "../component/tooltip_input";
import schemas from "../react/schemas";
import ui from "./ui";
import {AbsoluteTime} from "../render/format_times";
import {ExperimentTypes} from "./constants";
import {coalesce, isDefinedAndNotNull} from "../utils";

const ExperimentInputProperties = function (props) {
  const isAiExperiment = ui.isAiExperiment(props.experimentInput);
  return (
    <div>
      <TooltipInput
        className="name-input"
        label="Name"
        placeholder="Experiment Name"
        setter={props.experimentSetter("name")}
        tooltip="Pick something memorable!"
        value={props.experimentInput.name || ""}
      />
      <TooltipInput
        label={isAiExperiment ? "Budget" : "Observation Budget"}
        placeholder={isAiExperiment ? "Budget" : "Observation Budget"}
        setter={props.experimentSetter(
          isAiExperiment ? "budget" : "observation_budget",
        )}
        tooltip={
          `How many ${
            isAiExperiment ? "runs" : "observations"
          } you intend to create.` +
          " This is optional but improves the quality of your experiment."
        }
        value={coalesce(
          isAiExperiment
            ? props.experimentInput.budget
            : props.experimentInput.observation_budget,
          "",
        ).toString()}
      />
      <TooltipInput
        className="parallel-bandwidth-input"
        label="Parallel Bandwidth"
        placeholder="1"
        setter={props.experimentSetter("parallel_bandwidth")}
        tooltip={
          "How many suggestions you intend to run simultaneously." +
          " This is optional but improves the quality of your suggestions."
        }
        value={coalesce(
          props.experimentInput.parallel_bandwidth,
          "",
        ).toString()}
      />
    </div>
  );
};
ExperimentInputProperties.propTypes = {
  experimentInput: PropTypes.object.isRequired,
  experimentSetter: PropTypes.func.isRequired,
};

const ExperimentReadOnlyProperties = function (props) {
  const isAiExperiment = ui.isAiExperiment(props.experimentInput);
  return (
    <div className="table-responsive experiment-table-holder">
      <table className="table">
        <tbody>
          <tr>
            <th>ID</th>
            <td>{props.experimentInput.id}</td>
          </tr>
          <tr>
            <th>Name</th>
            <td>{props.experimentInput.name}</td>
          </tr>
          <tr>
            <th>Type</th>
            <td>
              {props.experimentInput.type === ExperimentTypes.OFFLINE
                ? `${props.experimentInput.type} (default)`
                : props.experimentInput.type}
            </td>
          </tr>
          <tr>
            <th>Created</th>
            <td>{<AbsoluteTime time={props.experimentInput.created} />}</td>
          </tr>
          {props.creator && (
            <tr>
              <th>Created By</th>
              <td>{props.creator.name}</td>
            </tr>
          )}
          {(isDefinedAndNotNull(props.experimentInput.observation_budget) ||
            isDefinedAndNotNull(props.experimentInput.budget)) && (
            <tr>
              <th>
                <Tooltip
                  tooltip={
                    `Let us know how many ${
                      isAiExperiment ? "runs" : "observations"
                    } you plan to create so that we can optimize our` +
                    " optimization strategy. We recommend a value between 10x-20x the number of parameters."
                  }
                >
                  {isAiExperiment ? "Budget" : "Observation Budget"}
                </Tooltip>
              </th>
              <td>
                {isAiExperiment
                  ? props.experimentInput.budget
                  : props.experimentInput.observation_budget}
              </td>
            </tr>
          )}
          {isDefinedAndNotNull(props.experimentInput.parallel_bandwidth) && (
            <tr>
              <th>
                <Tooltip
                  tooltip={
                    "The number of simultaneous suggestions you expect to run.  By default, we assume" +
                    " parallel bandwidth is 1, i.e., suggestions are executed sequentially."
                  }
                >
                  Parallel Bandwidth
                </Tooltip>
              </th>
              <td>{props.experimentInput.parallel_bandwidth}</td>
            </tr>
          )}
          {isDefinedAndNotNull(props.experimentInput.num_solutions) && (
            <tr>
              <th>
                <Tooltip tooltip="The number of sufficiently diverse solutions that we will attempt to find.">
                  Number of Solutions
                </Tooltip>
              </th>
              <td>{props.experimentInput.num_solutions}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};
ExperimentReadOnlyProperties.propTypes = {
  creator: schemas.User,
  experimentInput: PropTypes.object.isRequired,
};

export const ExperimentPropertiesSection = function (props) {
  const editing = ui.inputInteraction(props.interactionState);
  return editing ? (
    <ExperimentInputProperties
      clientId={props.clientId}
      experimentInput={props.experimentInput}
      experimentSetter={props.experimentSetter}
    />
  ) : (
    <ExperimentReadOnlyProperties
      creator={props.creator}
      experimentInput={props.experimentInput}
    />
  );
};
