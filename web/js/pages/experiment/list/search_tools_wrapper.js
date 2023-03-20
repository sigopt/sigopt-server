/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";
import pluralize from "pluralize";

import {FilterButtonHolder} from "./buttons";

const SearchMetadata = function (props) {
  const resultStr = pluralize("result", props.count, true);
  const metadata =
    props.total && props.count
      ? `${resultStr} found out of ${props.total}.`
      : "";
  return (
    <div className="search-metadata-holder">
      {metadata}{" "}
      <a className="nav-link" onClick={() => props.resetToDashboard()}>
        {props.isProjectPage
          ? "Reset project search."
          : "Return to my experiments."}
      </a>
    </div>
  );
};

SearchMetadata.propTypes = {
  count: PropTypes.number,
  isProjectPage: PropTypes.bool.isRequired,
  resetToDashboard: PropTypes.func.isRequired,
  total: PropTypes.number,
};

export default class SearchToolsWrapper extends React.Component {
  static propTypes = {
    archived: PropTypes.bool.isRequired,
    clearSelectedExperiments: PropTypes.func.isRequired,
    dev: PropTypes.bool.isRequired,
    experimentListFetcher: PropTypes.func.isRequired,
    includeClient: PropTypes.bool.isRequired,
    isAiExperiment: PropTypes.bool.isRequired,
    isDashboard: PropTypes.bool.isRequired,
    isProjectPage: PropTypes.bool.isRequired,
    pushViewHistory: PropTypes.func.isRequired,
    resetToDashboard: PropTypes.func.isRequired,
    searchCount: PropTypes.number,
    showClientExperiments: PropTypes.bool,
  };

  state = {
    searchTotal: undefined,
  };

  componentDidMount() {
    this.props.experimentListFetcher(
      {
        limit: 0,
        state: "all",
      },
      (response) => this.setState({searchTotal: response.count}),
    );
  }

  render() {
    return (
      <div className="search-tools-wrapper">
        {this.props.isDashboard ? (
          <FilterButtonHolder
            archived={this.props.archived}
            clearSelectedExperiments={this.props.clearSelectedExperiments}
            dev={this.props.dev}
            includeClient={this.props.includeClient}
            isAiExperiment={this.props.isAiExperiment}
            isProjectPage={this.props.isProjectPage}
            pushViewHistory={this.props.pushViewHistory}
            showClientExperiments={this.props.showClientExperiments}
          />
        ) : (
          <SearchMetadata
            count={this.props.searchCount}
            isProjectPage={this.props.isProjectPage}
            resetToDashboard={this.props.resetToDashboard}
            total={this.state.searchTotal}
          />
        )}
      </div>
    );
  }
}
