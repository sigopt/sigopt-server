/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/experiment/list.less";

import React from "react";

import ExperimentList from "./list";
import PageBody from "../../../component/page_body";
import PageTitle from "../../../component/page_title";
import SearchBox from "../../../experiment/search_box";
import SearchToolsWrapper from "./search_tools_wrapper";
import makeExperimentListController from "./controller";
import {BulkActionButtonHolder} from "./buttons";
import {EXPERIMENT_LIST_TYPE} from "./constants";

export default makeExperimentListController(
  EXPERIMENT_LIST_TYPE.clients,
  class extends React.Component {
    static displayName = "ExperimentListPage";

    constructor(props, context) {
      super(props, context);
      this._modal = React.createRef();
    }

    componentDidMount() {
      if (this._modal.current) {
        this._modal.current.show();
      }
    }

    render() {
      const pageTitle = this.props.pageTitle;
      return (
        <div className="experiment-list logged-in-page">
          <PageTitle gradientStyle="experiment" title={pageTitle} />
          <PageBody>
            <SearchBox {...this.props.searchBoxProps} />
            <SearchToolsWrapper {...this.props.searchToolsWrapperProps} />
            <BulkActionButtonHolder
              {...this.props.bulkActionButtonHolderProps}
            />
            <ExperimentList {...this.props.experimentListProps} />
          </PageBody>
        </div>
      );
    }
  },
);
