/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/project_page.less";

import _ from "underscore";
import React from "react";

import ExperimentList from "../../experiment/list/list";
import ProjectPage from "../page_wrapper";
import SearchBox from "../../../experiment/search_box";
import SearchToolsWrapper from "../../experiment/list/search_tools_wrapper";
import SourcePool from "../../../net/pool";
import makeExperimentListController from "../../experiment/list/controller";
import {
  AsynchronousUserDataSource,
  AvailableUserDataSource,
} from "../../../user/data_source";
import {BulkActionButtonHolder} from "../../experiment/list/buttons";
import {EXPERIMENT_LIST_TYPE} from "../../experiment/list/constants";

export default makeExperimentListController(
  EXPERIMENT_LIST_TYPE.projects,
  class ProjectAiExperiments extends React.Component {
    constructor(props) {
      super(props);
      this.state = {
        projectName: this.props.project.name,
      };
      this.userDataSources = new SourcePool((key) =>
        key === this.props.currentUser.id
          ? new AvailableUserDataSource(key, this.props)
          : new AsynchronousUserDataSource(key, this.props),
      );
    }

    render() {
      return (
        <ProjectPage {...this.props}>
          <div className="experiment-list">
            <SearchBox {...this.props.searchBoxProps} />
            <SearchToolsWrapper {...this.props.searchToolsWrapperProps} />
            <BulkActionButtonHolder
              {...this.props.bulkActionButtonHolderProps}
            />
            <ExperimentList
              {..._.extend({}, this.props.experimentListProps, {
                includeClient: true,
              })}
            />
          </div>
        </ProjectPage>
      );
    }
  },
);
