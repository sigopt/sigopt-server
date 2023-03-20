/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/project_runs_analysis_page.less";

import React from "react";
import {Provider} from "react-redux";

import ProjectPage from "../page_wrapper";
import {ConnectedRunsDashboard} from "./dashboard/runs_dashboard";
import {createDashBoardStore} from "./state/store";

export default class ProjectRunsAnalysis extends React.Component {
  constructor(props) {
    super(props);

    const store = createDashBoardStore(
      props.project,
      props.client,
      props.currentUser,
      props.promiseApiClient,
    );

    this.state = {
      store,
    };
  }

  render() {
    return (
      <ProjectPage {...this.props}>
        <div className="dashboard-wrapper">
          <Provider store={this.state.store}>
            <ConnectedRunsDashboard />
          </Provider>
        </div>
      </ProjectPage>
    );
  }
}
