/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/project_runs_page_local.less";

import React from "react";
import {Provider, connect} from "react-redux";

import Component from "../../../react/component";
import {ConnectedRunsTable} from "../components/runs_table/runs_table";
import {changeFilterModel, fetchRuns} from "../state/dimensions_slice";
import {createRunsStore} from "./store";
import {fetchViews} from "../state/views_slice";

class Fetcher extends React.Component {
  componentDidMount() {
    this.props.fetchRuns(null, null, this.props.experimentId);
    this.props.fetchViews();
  }

  componentDidUpdate() {
    // Have to do a bit of extra work to reuse logic from analysis page
    if (this.props.definedFields && this.props.filterModel === null) {
      this.props.changeFilterModel({});
    }
  }

  render() {
    return null;
  }
}

const mapStateToProps = (state) => ({
  filterModel: state.dimensions.filterModel,
  definedFields: state.dimensions.definedFields,
});

const ConnectedFetcher = connect(mapStateToProps, {
  fetchRuns,
  fetchViews,
  changeFilterModel,
})(Fetcher);

class ProjectRunsTable extends Component {
  constructor(props) {
    super(props);

    const store = createRunsStore(
      this.props.project,
      this.props.client,
      this.props.user,
      this.props.promiseApiClient,
    );

    this.state = {store};
  }

  render() {
    const expId = this.props.experiment ? this.props.experiment.id : null;
    return (
      <div className="run-table">
        {this.state.store && (
          <Provider store={this.state.store}>
            <ConnectedFetcher experimentId={expId} />
            <ConnectedRunsTable
              disableViews={this.props.disableViews || false}
              sortColumns={this.props.sortColumns}
              organizationId={this.props.organizationId}
            />
          </Provider>
        )}
      </div>
    );
  }
}

export {ProjectRunsTable};
