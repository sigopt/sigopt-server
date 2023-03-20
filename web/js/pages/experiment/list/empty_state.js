/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import AIQuickStartGuide from "./ai_quick_start_guide";
import CoreQuickStartGuide from "./core_quick_start_guide";

export default (props) => {
  if (props.dev) {
    return (
      <p className="no-experiments">
        There are no development experiments
        {props.isProjectPage && " in this project"}.
      </p>
    );
  } else if (props.includeClient && props.archived) {
    return (
      <p className="no-experiments">
        Your team does not have any archived experiments
        {props.isProjectPage && " in this project"}.
      </p>
    );
  } else if (!props.includeClient && props.archived) {
    return (
      <p className="no-experiments">
        You have not yet archived any experiments
        {props.isProjectPage && " in this project"}.
      </p>
    );
  } else if (props.includeClient) {
    let message = null;
    if (props.isProjectPage) {
      message =
        "Once you or a member of your team adds or creates an experiment you'll see it here!";
    } else {
      message =
        "Once a member of your team creates an experiment you'll see it here!";
    }
    return (
      <p className="no-experiments">
        Your team does not have any active experiments
        {props.isProjectPage && " in this project"}. {message}
      </p>
    );
  } else if (props.pageQuery.length !== 0) {
    return (
      <p className="no-experiments">
        Your search matches no experiments
        {props.isProjectPage && " in this project"}.
      </p>
    );
  } else if (props.canEdit) {
    return (
      <div className="no-experiments">
        {props.isAiExperiment ? (
          <AIQuickStartGuide
            apiToken={props.apiToken}
            projectId={props.project ? props.project.id : "sigopt-examples"}
          />
        ) : (
          <CoreQuickStartGuide />
        )}
      </div>
    );
  } else {
    return (
      <p className="no-experiments">
        Read-only users cannot create new experiments.
      </p>
    );
  }
};
