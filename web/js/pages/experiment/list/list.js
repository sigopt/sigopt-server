/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import EmptyState from "./empty_state";
import ExperimentRow from "./row";
import Header from "../../../table/header";
import Loading from "../../../component/loading";
import PagingBlock from "../../../pagination/paging-block";
import PagingTable from "../../../pagination/paging-table";
import makePageable from "../../../pagination/make-pageable";
import schemas from "../../../react/schemas";
import {EXPERIMENT_STATE_ENUM} from "./constants";

const pageFetcher = function (paging, success, error) {
  if (this.props.pageQuery.length === 0) {
    _.extend(paging, {
      state: this.props.archived
        ? EXPERIMENT_STATE_ENUM.all
        : EXPERIMENT_STATE_ENUM.active,
      user: this.props.includeClient ? null : this.props.user,
      development: this.props.dev ? null : false,
      sort: "recent",
    });
  } else {
    _.extend(paging, {
      search: this.props.pageQuery,
      state: "all",
      sort: "recent",
    });
  }
  this.props.experimentListFetcher(
    paging,
    (response) => {
      if (this.props.pageQuery) {
        this.props.onReceiveSearchCount(response.count);
      }
      success(response);
    },
    error,
  );
};

const SelectAllCheckbox = function (props) {
  return (
    <div className="checkbox">
      <input
        type="checkbox"
        id="checkbox-experiments"
        checked={props.anySelected}
        onChange={props.toggleAllSelectedExperiments}
      />
      <label htmlFor="checkbox-experiments" />
    </div>
  );
};

SelectAllCheckbox.propTypes = {
  anySelected: PropTypes.bool.isRequired,
  toggleAllSelectedExperiments: PropTypes.func.isRequired,
};

const ExperimentList = makePageable(
  pageFetcher,
  class ExperimentList extends React.Component {
    static propTypes = {
      apiToken: PropTypes.string.isRequired,
      archived: PropTypes.bool.isRequired,
      canEdit: PropTypes.bool.isRequired,
      canShare: PropTypes.bool.isRequired,
      data: PropTypes.arrayOf(schemas.Experiment),
      dev: PropTypes.bool.isRequired,
      experimentListFetcher: PropTypes.func.isRequired,
      freshPageNonce: PropTypes.number,
      historyTracker: PropTypes.object.isRequired,
      includeClient: PropTypes.bool.isRequired,
      includeProject: PropTypes.bool.isRequired,
      isAiExperiment: PropTypes.bool,
      isProjectPage: PropTypes.bool.isRequired,
      loginState: schemas.LoginState.isRequired,
      navigateToPage: PropTypes.func.isRequired,
      onReceiveSearchCount: PropTypes.func.isRequired,
      pageQuery: PropTypes.string.isRequired,
      project: schemas.Project,
      refreshPage: PropTypes.func.isRequired,
      reloadPages: PropTypes.func.isRequired,
      selectedExperiments: PropTypes.object.isRequired,
      startPage: PropTypes.number.isRequired,
      toggleAllSelectedExperiments: PropTypes.func.isRequired,
      toggleExperimentSelection: PropTypes.func.isRequired,
      updateExperimentsOnPage: PropTypes.func.isRequired,
      user: PropTypes.string,
      userDataSources: PropTypes.object.isRequired,
    };

    componentDidMount() {
      this.props.historyTracker.addHandler(
        "page",
        (pageNumber) => this.props.navigateToPage(pageNumber, false),
        this.props.startPage,
      );
    }

    componentDidUpdate(prevProps) {
      if (
        prevProps.pageQuery !== this.props.pageQuery ||
        prevProps.includeClient !== this.props.includeClient ||
        prevProps.archived !== this.props.archived ||
        prevProps.dev !== this.props.dev
      ) {
        this.props.reloadPages(this.props.startPage);
      } else if (prevProps.freshPageNonce !== this.props.freshPageNonce) {
        this.props.refreshPage();
      }
      if (prevProps.data !== this.props.data) {
        this.props.updateExperimentsOnPage(this.props.data);
      }
    }

    forceReload = () => {
      this.props.reloadPages(this.props.startPage);
    };

    render() {
      const showCreatedBy =
        this.props.includeClient === true || this.props.pageQuery.length > 0;
      return (
        <div
          className="experiments"
          data-experiment-view={this.props.includeClient ? "team" : "mine"}
        >
          <div className="table-holder">
            <Loading
              loading={!this.props.data}
              empty={_.size(this.props.data) === 0}
              emptyMessage={<EmptyState {...this.props} />}
            >
              <PagingTable
                {...this.props}
                className="table experiment-table"
                head={
                  <thead>
                    <tr>
                      <Header>
                        <SelectAllCheckbox
                          anySelected={
                            _.size(this.props.selectedExperiments) > 0
                          }
                          toggleAllSelectedExperiments={
                            this.props.toggleAllSelectedExperiments
                          }
                        />
                      </Header>
                      <Header>ID</Header>
                      <Header>Name</Header>
                      <Header>Progress</Header>
                      <Header>Best Value</Header>
                      <Header />
                      {/* archived label */}
                      <Header />
                      {/* dev label */}
                      <Header>Last Updated</Header>
                      {this.props.includeProject &&
                      this.props.isAiExperiment ? (
                        <Header>Project ID</Header>
                      ) : null}
                      {showCreatedBy ? <Header>Created By</Header> : null}
                      <Header />
                      {/* archive/share buttons */}
                    </tr>
                  </thead>
                }
              >
                {_.map(this.props.data, (experiment) => (
                  <ExperimentRow
                    canEdit={this.props.canEdit}
                    canShare={this.props.canShare}
                    experiment={experiment}
                    showCreatedBy={showCreatedBy}
                    includeProject={this.props.includeProject}
                    key={experiment.id}
                    reload={this.props.refreshPage}
                    toggleExperimentSelection={
                      this.props.toggleExperimentSelection
                    }
                    selected={_.has(
                      this.props.selectedExperiments,
                      experiment.id,
                    )}
                    userDataSources={this.props.userDataSources}
                    isAiExperiment={this.props.isAiExperiment}
                  />
                ))}
              </PagingTable>
            </Loading>
          </div>
          <div className="paging-holder">
            <PagingBlock {...this.props} />
          </div>
        </div>
      );
    }
  },
);

export default ExperimentList;
