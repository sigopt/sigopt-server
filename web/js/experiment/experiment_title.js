/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./experiment_title.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import schemas from "../react/schemas.js";
import PageTitle, {TitlePropTypes} from "../component/page_title.js";
import {ExperimentBudgetProgressBar} from "./runs_progress_bar";

export default function ExperimentTitle(props) {
  return (
    <PageTitle {..._.omit(props, "info")} hideBorder={true}>
      <div className="experiment-title-row">
        <div className="info">{props.info}</div>
        <ExperimentBudgetProgressBar
          experiment={props.experiment}
          failedRuns={props.failedRuns}
        />
      </div>
      {props.children && (
        <div className="experiment-navbar">{props.children}</div>
      )}
    </PageTitle>
  );
}

ExperimentTitle.propTypes = {
  ...TitlePropTypes,
  failedRuns: PropTypes.number,
  promiseApiClient: schemas.PromiseApiClient.isRequired,
};
