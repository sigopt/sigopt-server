/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/projects_page.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import smoothscroll from "smoothscroll";

import CreateProjectButton from "../projects/create_project_button";
import HistoryTracker from "../../net/history";
import Loading from "../../component/loading";
import PageBody from "../../component/page_body";
import PageTitle from "../../component/page_title";
import PagingBlock from "../../pagination/paging-block";
import ParsedUrl from "../../net/url";
import ProjectTile from "../../project/tile";
import SourcePool from "../../net/pool";
import makePageable from "../../pagination/make-pageable";
import schemas from "../../react/schemas";
import {
  AsynchronousUserDataSource,
  AvailableUserDataSource,
} from "../../user/data_source";
import {FilterCheckbox, ViewToggle} from "../experiment/list/buttons";
import {coalesce, isPositiveInteger, maybeAsNumber} from "../../utils";

const pageFetcher = function (paging, success, error) {
  _.extend(paging, {
    user: this.state.includeClient ? null : this.props.loginState.userId,
    deleted: this.state.showArchived,
  });
  this.props.promiseApiClient
    .clients(this.props.loginState.clientId)
    .projects()
    .fetch(paging)
    .then(success, error);
};

const ProjectsPage = makePageable(
  pageFetcher,
  class ProjectsPage extends React.Component {
    static propTypes = {
      currentPage: PropTypes.number,
      currentPermission: schemas.Permission,
      currentUser: schemas.User,
      data: PropTypes.arrayOf(PropTypes.object),
      emptyState: PropTypes.node,
      loginState: schemas.LoginState,
      navigateToPage: PropTypes.func.isRequired,
      pageParams: PropTypes.object,
      pageSize: PropTypes.number,
      reloadPages: PropTypes.func.isRequired,
    };

    static defaultProps = {
      emptyState: (
        <p>There aren&rsquo;t any projects. Feel free to create one.</p>
      ),
      pageSize: 12,
      startPage: 0,
    };

    constructor(props) {
      super(props);
      const validatedPageParams = this.validatePageParams(props.pageParams);
      this.state = _.defaults(validatedPageParams, {
        includeClient: false,
        page: 0,
        showArchived: false,
      });
      this.currentPage = this.state.page;
      this.historyTracker = new HistoryTracker();
      this.userDataSources = new SourcePool((key) =>
        key === this.props.currentUser.id
          ? new AvailableUserDataSource(key, this.props)
          : new AsynchronousUserDataSource(key, this.props),
      );
    }

    componentDidMount() {
      this.historyTracker.addHandler(
        "includeClient",
        (includeClient) =>
          this.setState({
            includeClient: includeClient,
            page: this.currentPage,
          }),
        this.state.includeClient,
      );
      this.historyTracker.addHandler(
        "page",
        (pageNumber) => this.props.navigateToPage(pageNumber, false),
        this.state.page,
      );
    }

    componentDidUpdate(prevProps, prevState) {
      if (prevState.includeClient !== this.state.includeClient) {
        this.props.reloadPages(this.state.page);
      }
    }

    validatePageParams = (pageParams) => {
      let params = _.clone(pageParams);

      if (_.has(params, "includeClient")) {
        params = params.includeClient
          ? _.extend(params, {includeClient: true})
          : _.omit(params, "includeClient");
      }

      if (_.has(params, "page")) {
        const pageNumber = maybeAsNumber(params.page);
        params = isPositiveInteger(pageNumber)
          ? _.extend(params, {page: pageNumber})
          : _.omit(params, "page");
      }

      return params;
    };

    pageUpdated = (urlParams, changeHistory) => {
      const includeClient = coalesce(
        urlParams.includeClient,
        this.state.includeClient,
        false,
      );
      const newPage = coalesce(urlParams.page, this.state.page, 0);

      this.currentPage = newPage;

      const params = _.extend({page: newPage}, {includeClient: includeClient});
      const newUrl = new ParsedUrl();
      newUrl.params = params;

      if (changeHistory) {
        this.historyTracker.pushState(
          _.extend(urlParams, {
            includeClient: this.state.includeClient,
          }),
          newUrl.toString(),
        );
      }
    };

    pushViewHistory = (view) => {
      smoothscroll(0);
      const params = _.extend({}, view, {page: 0});
      this.setState(params, () => {
        this.pageUpdated(params, true);
      });
    };

    onToggleIncludeClient = () => {
      this.pushViewHistory({includeClient: !this.state.includeClient});
    };

    emptyState() {
      if (this.state.includeClient) {
        return (
          <p className="no-projects">
            Your team does not have any projects. Once a member of your team
            creates a project you&rsquo;ll see it here!
          </p>
        );
      } else {
        return (
          <p className="no-projects">
            You don&rsquo;t have any projects. Once you create a project
            you&rsquo;ll see it here!
          </p>
        );
      }
    }

    toggleArchived = () =>
      this.setState(
        (state) => ({showArchived: !state.showArchived}),
        this.props.reloadPages,
      );

    render() {
      const canSeeExperimentsByOthers = Boolean(
        this.props.currentPermission &&
          this.props.currentPermission.can_see_experiments_by_others,
      );

      return (
        <div className="project-page">
          <PageTitle
            gradientStyle="project"
            secondaryButtons={
              <CreateProjectButton className="btn-inverse" {...this.props} />
            }
            title="AI Projects"
          />
          <PageBody>
            <div className="projects-page-controls">
              <div className="projects-view-button-holder">
                {canSeeExperimentsByOthers && (
                  <ViewToggle
                    includeClient={this.state.includeClient}
                    onToggle={this.onToggleIncludeClient}
                  />
                )}
              </div>
              <div className="projects-show-archived-holder">
                <FilterCheckbox
                  label="Show Archived"
                  checked={this.state.showArchived}
                  onClick={this.toggleArchived}
                />
              </div>
              {this.props.data && <PagingBlock {...this.props} />}
            </div>
            <Loading
              loading={!this.props.data}
              empty={_.isEmpty(this.props.data)}
              emptyMessage={this.emptyState()}
            >
              <div
                className="projects"
                data-project-view={this.state.includeClient ? "team" : "mine"}
              >
                {_.map(this.props.data, (project) => (
                  <ProjectTile
                    {...this.props}
                    includeClient={this.state.includeClient}
                    key={project.id}
                    project={project}
                    userDataSources={this.userDataSources}
                  />
                ))}
              </div>
              <PagingBlock {...this.props} />
            </Loading>
          </PageBody>
        </div>
      );
    }
  },
);

export default ProjectsPage;
