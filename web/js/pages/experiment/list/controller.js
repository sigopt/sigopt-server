/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import smoothscroll from "smoothscroll";

import HistoryTracker from "../../../net/history";
import ParsedUrl from "../../../net/url";
import SourcePool from "../../../net/pool";
import schemas from "../../../react/schemas";
import {
  AsynchronousUserDataSource,
  AvailableUserDataSource,
} from "../../../user/data_source";
import {EXPERIMENT_LIST_TYPE} from "./constants";
import {coalesce, isPositiveInteger, maybeAsNumber} from "../../../utils";

export default (listType, WrappedComponent) =>
  class ExperimentListController extends React.Component {
    static propTypes = {
      alertBroker: schemas.AlertBroker.isRequired,
      apiToken: PropTypes.string.isRequired,
      apiUrl: PropTypes.string,
      canShare: PropTypes.bool,
      client: schemas.Client.isRequired,
      currentPermission: schemas.Permission.isRequired,
      currentUser: schemas.User.isRequired,
      isAiExperiment: PropTypes.bool,
      loginState: schemas.LoginState.isRequired,
      mineExperimentCount: PropTypes.number,
      navigator: schemas.Navigator.isRequired,
      pageParams: PropTypes.object,
      project: schemas.Project,
      promiseApiClient: schemas.PromiseApiClient.isRequired,
      teamExperimentCount: PropTypes.number,
    };

    constructor(props, context) {
      super(props, context);
      const validatedPageParams = this.validatePageParams(props.pageParams);
      const filteredView =
        validatedPageParams.archived || validatedPageParams.dev;
      const includeClient = filteredView
        ? validatedPageParams.includeClient || false
        : this.props.mineExperimentCount === 0 &&
          this.props.teamExperimentCount > 0;
      this.state = _.defaults(validatedPageParams, {
        archived: false,
        bulkActionLoading: false,
        dev: false,
        experimentsOnPage: {},
        freshPageNonce: 1,
        includeClient: includeClient,
        includeProject: listType !== EXPERIMENT_LIST_TYPE.projects,
        page: 0,
        projectNonce: 1,
        query: "",
        searchCount: undefined,
        selectedExperiments: {},
      });

      this.currentPage = this.state.page;

      this._list = React.createRef();

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
            query: "",
            page: this.currentPage,
          }),
        this.state.includeClient,
      );
      this.historyTracker.addHandler(
        "archived",
        (archived) =>
          this.setState({
            archived: archived,
            query: "",
            page: this.currentPage,
          }),
        this.state.archived,
      );
      this.historyTracker.addHandler(
        "dev",
        (dev) =>
          this.setState({
            dev: dev,
            query: "",
            page: this.currentPage,
          }),
        this.state.dev,
      );
      this.historyTracker.addHandler(
        "query",
        (query) => {
          this.setState({
            query: query,
            page: this.currentPage,
            includeClient: false,
            archived: false,
            dev: false,
          });
        },
        this.state.query,
      );
    }

    onReceiveSearchCount = (searchCount) => {
      this.setState({searchCount: searchCount});
    };

    validatePageParams = (pageParams) => {
      let params = _.clone(pageParams);

      if (_.has(params, "includeClient")) {
        params = params.includeClient
          ? _.extend(params, {includeClient: true})
          : _.omit(params, "includeClient");
      }

      if (_.has(params, "archived")) {
        params = params.archived
          ? _.extend(params, {archived: true})
          : _.omit(params, "archived");
      }

      if (_.has(params, "dev")) {
        params = params.dev
          ? _.extend(params, {dev: true})
          : _.omit(params, "dev");
      }

      if (_.has(params, "page")) {
        const pageNumber = maybeAsNumber(params.page);
        params = isPositiveInteger(pageNumber)
          ? _.extend(params, {page: pageNumber})
          : _.omit(params, "page");
      }

      return params;
    };

    pushViewHistory = (view) => {
      smoothscroll(0);
      const params = _.extend({}, view, {query: "", page: 0});
      this.setState(params, () => {
        this.pageUpdated(params, true);
      });
    };

    resetToDashboard = () => {
      smoothscroll(0);
      const params = {
        query: "",
        page: 0,
        includeClient: false,
        archived: false,
        dev: false,
        selectedExperiments: {},
      };
      const urlParams = _.omit(params, "selectedExperiments");
      this.setState(params, () => {
        this.pageUpdated(urlParams, true);
      });
    };

    pageUpdated = (urlParams, changeHistory) => {
      const includeClient = coalesce(
        urlParams.includeClient,
        this.state.includeClient,
        false,
      );
      const archived = coalesce(urlParams.archived, this.state.archived, false);
      const dev = coalesce(urlParams.dev, this.state.dev, false);
      const newPage = coalesce(urlParams.page, this.state.page, 0);
      const newQuery = coalesce(urlParams.query, this.state.query, "");

      this.currentPage = newPage;

      const params = _.extend(
        {page: newPage},
        newQuery.length === 0
          ? _.pick(
              {includeClient: includeClient, archived: archived, dev: dev},
              _.identity,
            )
          : {query: newQuery},
      );
      const newUrl = new ParsedUrl();
      newUrl.params = params;

      if (changeHistory) {
        this.historyTracker.pushState(
          _.extend(urlParams, {
            includeClient: this.state.includeClient,
            archived: this.state.archived,
            dev: this.state.dev,
            query: this.state.query,
          }),
          newUrl.toString(),
        );
      }
    };

    clearSelectedExperiments = () => this.setState({selectedExperiments: {}});

    updateExperimentsOnPage = (experiments) =>
      this.setState({
        experimentsOnPage: _.object(_.map(experiments, (e) => [e.id, true])),
      });

    toggleAllSelectedExperiments = () => {
      const allChecked = _.all(
        _.keys(this.state.experimentsOnPage),
        (e) => this.state.selectedExperiments[e],
      );
      if (allChecked) {
        this.clearSelectedExperiments();
      } else {
        this.setState((prevState) => ({
          selectedExperiments: _.extend(
            {},
            prevState.selectedExperiments,
            prevState.experimentsOnPage,
          ),
        }));
      }
    };

    toggleExperimentSelection = (experimentId, selected) => {
      this.setState((prevState) => ({
        selectedExperiments: selected
          ? _.extend({}, prevState.selectedExperiments, {[experimentId]: true})
          : _.omit(prevState.selectedExperiments, experimentId),
      }));
    };

    refreshPage = () =>
      this.setState(
        {
          bulkActionLoading: false,
          freshPageNonce: Math.random(),
        },
        this.clearSelectedExperiments,
      );

    _bulkAction =
      (promiseFunction, completedCallback) =>
      (...args) => {
        if (!this.state.bulkActionLoading) {
          this.setState({bulkActionLoading: true}, () =>
            Promise.all(
              _.map(_.keys(this.state.selectedExperiments), (experimentId) =>
                promiseFunction(experimentId, ...args),
              ),
            )
              .then(this.refreshPage, (err) => {
                this.setState({bulkActionLoading: false});
                return Promise.reject(err);
              })
              .then(() =>
                _.isFunction(completedCallback) ? completedCallback() : null,
              ),
          );
        }
      };

    getExperimentEndpoint = (experimentId) =>
      this.props.isAiExperiment
        ? this.props.promiseApiClient.aiexperiments(experimentId)
        : this.props.promiseApiClient.experiments(experimentId);

    // TODO: should this be batched?
    archiveSelectedExperiments = this._bulkAction((experimentId) =>
      this.getExperimentEndpoint(experimentId).delete(),
    );

    // TODO: should this be batched?
    unarchiveSelectedExperiments = this._bulkAction((experimentId) =>
      this.getExperimentEndpoint(experimentId).update({state: "active"}),
    );

    getSearchResults = (query) => {
      smoothscroll(0);
      const params = {
        query: query,
        page: 0,
        includeClient: false,
        archived: false,
        dev: false,
        selectedExperiments: {},
      };
      const urlParams = _.omit(params, "selectedExperiments");
      this.setState(params, () => {
        this._list.current.getInstance().forceReload();
        this.pageUpdated(urlParams, true);
      });
    };

    experimentListFetcher = (paging, success, error) => {
      const endpoint = this.props.promiseApiClient.clients(
        this.props.client.id,
      );

      return this.props.isAiExperiment
        ? endpoint.aiexperiments().fetch(paging).then(success, error)
        : endpoint
            .experiments()
            .fetch({...paging, include_ai: false})
            .then(success, error);
    };

    render() {
      const canSeeExperimentsByOthers = Boolean(
        this.props.currentPermission &&
          this.props.currentPermission.can_see_experiments_by_others,
      );
      const canEdit = Boolean(
        this.props.currentPermission && this.props.currentPermission.can_write,
      );
      return (
        <WrappedComponent
          {...this.props}
          canEdit={canEdit}
          canSeeExperimentsByOthers={canSeeExperimentsByOthers}
          searchBoxProps={{
            key: this.state.query,
            experimentListFetcher: this.experimentListFetcher,
            isProjectPage: listType === EXPERIMENT_LIST_TYPE.projects,
            name: "experiment-search",
            navigator: this.props.navigator,
            userDataSources: this.userDataSources,
            onSearchAll: this.getSearchResults,
            pageQuery: this.state.query,
            ref: this._searchBox,
          }}
          searchToolsWrapperProps={{
            archived: this.state.archived,
            clearSelectedExperiments: this.clearSelectedExperiments,
            experimentListFetcher: this.experimentListFetcher,
            includeClient: this.state.includeClient,
            pushViewHistory: this.pushViewHistory,
            showClientExperiments: canSeeExperimentsByOthers,
            dev: this.state.dev,
            searchCount: this.state.searchCount,
            isAiExperiment: this.props.isAiExperiment || false,
            isDashboard: this.state.query.length === 0,
            isProjectPage: listType === EXPERIMENT_LIST_TYPE.projects,
            resetToDashboard: this.resetToDashboard,
          }}
          bulkActionButtonHolderProps={{
            archiveSelectedExperiments: this.archiveSelectedExperiments,
            loading: this.state.bulkActionLoading,
            numSelected: _.size(this.state.selectedExperiments),
            unarchiveSelectedExperiments: this.unarchiveSelectedExperiments,
          }}
          experimentListProps={{
            alertBroker: this.props.alertBroker,
            apiToken: this.props.apiToken,
            apiUrl: this.props.apiUrl,
            archived: this.state.archived,
            canEdit: canEdit,
            canShare: this.props.canShare,
            dev: this.state.dev,
            experimentListFetcher: this.experimentListFetcher,
            freshPageNonce: this.state.freshPageNonce,
            historyTracker: this.historyTracker,
            includeClient: this.state.includeClient,
            includeProject: this.state.includeProject,
            isAiExperiment: this.props.isAiExperiment,
            isProjectPage: listType === EXPERIMENT_LIST_TYPE.projects,
            loginState: this.props.loginState,
            navigator: this.props.navigator,
            onReceiveSearchCount: this.onReceiveSearchCount,
            pageQuery: this.state.query,
            pageSize: 10,
            pageUpdated: this.pageUpdated,
            project: this.props.project,
            ref: this._list,
            selectedExperiments: this.state.selectedExperiments,
            startPage: this.state.page,
            toggleAllSelectedExperiments: this.toggleAllSelectedExperiments,
            toggleExperimentSelection: this.toggleExperimentSelection,
            updateExperimentsOnPage: this.updateExperimentsOnPage,
            user: this.props.loginState.userId,
            userDataSources: this.userDataSources,
          }}
        />
      );
    }
  };
