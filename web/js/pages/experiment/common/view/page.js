/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/view.less";
import "./page.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import pluralize from "pluralize";

import AddDataPrompt from "./add_data_prompt";
import BestAssignmentModal from "../../../../experiment/best_assignment_modal";
import Component from "../../../../react/component";
import DurationChart from "../../../../training_run/duration_chart";
import ExperimentImprovement from "../../../../react_chart/experiment_improvement/component";
import ExperimentPage from "../../page_wrapper";
import ExperimentSummary from "../../../../experiment/summary";
import Loading from "../../../../component/loading";
import ObservationModal from "../../../../experiment/observation_modal";
import Poller from "../../../../net/poller";
import PollingHistoryTable from "./polling_history_table";
import SignalGlyph from "../../../../component/glyph/signal";
import Tooltip from "../../../../component/tooltip";
import findClickedObservation from "../../../../experiment/find_clicked_observation.js";
import schemas from "../../../../react/schemas.js";
import sort_observations from "../../../../experiment/sort_observations";
import ui from "../../../../experiment/ui";
import RunsTable, {
  runDurationColumn,
  runIdColumn,
  runStatusColumn,
} from "../../../home/runs_table";
import {AxisTypes} from "../../../../chart/constants";
import {ChartTypes} from "../../../../react_chart/unified_constants";
import {DOCS_URL} from "../../../../net/constant";
import {ExperimentTypes} from "../../../../experiment/constants";
import {NewClientBanner} from "../../../../component/new_client_banner";
import {ObservationsProgressBar} from "./observation_progress_bar";
import {PRODUCT_NAME} from "../../../../brand/constant";
import {RunsProgressBar} from "../../../../experiment/runs_progress_bar";
import {UnifiedChart} from "../../../../react_chart/unified_chart";
import {getUnifiedChartArgs} from "../../../../react_chart/unified_chart_args";
import {isDefinedAndNotNull} from "../../../../utils";

const getRunColumns = (experiment) => {
  const columns = [runStatusColumn, runIdColumn, runDurationColumn];
  _.each(_.flatten([experiment.conditionals, experiment.parameters]), (param) =>
    columns.push({
      Header: () => <th>{param.name}</th>,
      Cell: ({run}) => (
        <td>{ui.renderParamValue(param, run.assignments[param.name], 6)}</td>
      ),
    }),
  );
  return columns;
};

const MoreGraphs = function (props) {
  return (
    <div className="share-experiment-holder">
      <a
        className="btn btn-white-border"
        href={ui.getExperimentUrl(props.experiment, "/analysis")}
      >
        <SignalGlyph /> More Graphs
      </a>
    </div>
  );
};

class ExperimentViewPage extends Component {
  static propTypes = {
    canEdit: PropTypes.bool,
    canShare: PropTypes.bool,
    experiment: schemas.Experiment.isRequired,
    isAiExperiment: PropTypes.bool.isRequired,
    isGuest: PropTypes.bool,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      activeRuns: null,
      bestAssignments: null,
      experiment: this.props.experiment,
      observations: null,
      recentObservations: null,
      stoppingCriteria: null,
    };
    this._bestAssignmentModal = React.createRef();
    this._observationModal = React.createRef();
  }

  componentDidMount() {
    const waitTime = 30000;

    this.experimentPoller = new Poller({
      poll: (success, error) =>
        this.services.legacyApiClient.experimentDetail(
          this.props.experiment.id,
          success,
          error,
        ),
      onChange: (experiment) =>
        experiment.updated > this.state.experiment.updated &&
        this.onUpdate(experiment),
      waitTime: waitTime,
    }).startOnce();

    this.onUpdate(this.state.experiment);
  }

  componentWillUnmount() {
    this.experimentPoller.stop();
  }

  onUpdate(experiment) {
    const logAndIgnoreErrors = (promise) =>
      promise.catch((e) => {
        this.services.errorNotifier.cleanupError(e);
        return null;
      });

    this.setState({experiment: experiment}, () => {
      Promise.all(
        _.map(
          [
            this.pollBestAssignments(experiment),
            this.pollObservations(experiment),
            this.pollRecentObservations(experiment),
            this.pollStoppingCriteria(experiment),
            this.props.isAiExperiment
              ? this.pollAllRuns(experiment)
              : Promise.resolve(null),
            this.props.isAiExperiment
              ? this.pollActiveRuns(experiment)
              : Promise.resolve(null),
          ],
          logAndIgnoreErrors,
        ),
      ).then(
        ([
          bestAssignments,
          observations,
          recentObservations,
          stoppingCriteria,
          allRuns,
          activeRuns,
        ]) => {
          this.setState({
            bestAssignments,
            observations,
            recentObservations,
            stoppingCriteria,
            allRuns,
            activeRuns,
          });
        },
      );
    });
  }

  pollRecentObservations = (experiment) =>
    this.services.promiseApiClient
      .experiments(experiment.id)
      .observations()
      .fetch({limit: 3})
      .then((pagination) => pagination.data);

  pollBestAssignments = (experiment) =>
    this.services.promiseApiClient
      .experiments(experiment.id)
      .bestAssignments()
      .exhaustivelyPage();

  pollObservations = (experiment) =>
    this.services.promiseApiClient
      .experiments(experiment.id)
      .observations()
      .exhaustivelyPage();

  pollStoppingCriteria = (experiment) =>
    this.services.promiseApiClient
      .experiments(experiment.id)
      .stoppingCriteria()
      .fetch();

  pollActiveRuns = (experiment) =>
    this.services.promiseApiClient
      .clients(experiment.client)
      .trainingRuns()
      .fetch({
        filters: JSON.stringify([
          {
            field: "experiment",
            operator: "==",
            value: experiment.id,
          },
          {
            field: "state",
            operator: "==",
            value: "active",
          },
        ]),
      });

  pollAllRuns = (experiment) =>
    this.services.promiseApiClient
      .clients(experiment.client)
      .projects(experiment.project)
      .trainingRuns()
      .exhaustivelyPage({
        filters: JSON.stringify([
          {
            operator: "==",
            field: "experiment",
            value: experiment.id,
          },
        ]),
      });

  showObservationOnChartClick = (data) => {
    const o = findClickedObservation(data, this.state.observations);
    if (this.props.isAiExperiment) {
      ui.navigateToRunForObservation(this.services, o.experiment, o.id);
    } else {
      this._observationModal.current.show(o);
    }
  };

  onSelectBestAssignment = (ba) => {
    if (this.props.isAiExperiment) {
      ui.navigateToRunForObservation(
        this.services,
        this.state.experiment.id,
        ba.id,
      );
    } else {
      this._bestAssignmentModal.current.show(ba);
    }
  };

  render() {
    const experiment = this.state.experiment;
    const progress = experiment.progress;
    const observations = this.state.observations;
    const activeRuns = this.state.activeRuns;
    const hasActiveRuns =
      isDefinedAndNotNull(activeRuns) && !_.isEmpty(activeRuns.data);
    const hasObservations =
      isDefinedAndNotNull(progress) && progress.observation_count > 0;

    const isParetoOptimizedExperiment = ui.isParetoOptimizedExperiment(
      this.props.experiment,
    );

    const observationProgress = (
      <div className="row">
        <ObservationsProgressBar experiment={experiment} />
      </div>
    );
    const newBudgetField = ui.isAiExperiment(this.state.experiment);
    const observationAlert = (
      <div className="row observation-warning">
        <div className="alert alert-warning">
          This experiment does not have a set{" "}
          {newBudgetField ? (
            "budget"
          ) : (
            <a href={`${DOCS_URL}/intro/main-concepts#observation-budget`}>
              observation budget
            </a>
          )}
          . While not required, setting{" "}
          {newBudgetField ? "a budget" : "an observation budget"} provides{" "}
          {PRODUCT_NAME} with more information and may lead to improved
          performance. You can set the{" "}
          {newBudgetField ? "budget" : "observation budget"} of this experiment
          via{" "}
          <a href={ui.getExperimentUrl(experiment, "/properties")}>
            the properties page
          </a>
          {""}.
        </div>
      </div>
    );

    const statusHeaders = [];
    const allFailures =
      !_.isEmpty(observations) && _.every(observations, (o) => o.failed);
    if (allFailures) {
      const failedObj = this.props.isAiExperiment ? "run" : "observation";
      const count = _.size(observations);
      statusHeaders.push(
        <div className="alert alert-danger">
          This experiment has {count} failed {pluralize(failedObj, count)} and 0
          successful {pluralize(failedObj, 0)}
        </div>,
      );
    }
    if (!this.props.isAiExperiment) {
      statusHeaders.push(<NewClientBanner />);
      if (newBudgetField && experiment.budget) {
        statusHeaders.push(
          <div className="row">
            <RunsProgressBar experiment={experiment} />
          </div>,
        );
      } else if (!newBudgetField && experiment.observation_budget) {
        statusHeaders.push(observationProgress);
      } else {
        statusHeaders.push(observationAlert);
      }
    }

    const renderedStatusHeader = _.map(statusHeaders, (h, i) => (
      <React.Fragment key={i}>{h}</React.Fragment>
    ));

    if (
      this.props.isAiExperiment
        ? progress.total_run_count === 0
        : !hasObservations && !hasActiveRuns
    ) {
      if (this.props.canEdit) {
        return (
          <ExperimentPage className="experiment-view-page" {...this.props}>
            {renderedStatusHeader}
            <AddDataPrompt
              canEdit={this.props.canEdit}
              experiment={experiment}
            />
          </ExperimentPage>
        );
      } else {
        return (
          <ExperimentPage className="experiment-view-page" {...this.props}>
            <div className="row">
              <div className="add-data-prompt">
                <p>
                  To get started, ask a user with write permissions to add some
                  data.
                </p>
              </div>
            </div>
          </ExperimentPage>
        );
      }
    }

    const visitHistory = (
      <div className="visit-history">
        <span>
          Visit the{" "}
          <a href={ui.getExperimentUrl(this.props.experiment, "/history")}>
            history page
          </a>{" "}
          to view{this.props.canEdit && " and edit"} all observations.
        </span>
      </div>
    );

    const finishedLoadingRuns = this.props.isAiExperiment
      ? isDefinedAndNotNull(this.state.allRuns)
      : true;

    const uniChartArgs =
      this.props.experiment &&
      observations &&
      this.state.bestAssignments &&
      finishedLoadingRuns &&
      getUnifiedChartArgs(
        this.props.experiment,
        observations,
        this.state.bestAssignments,
        this.props.isAiExperiment ? this.state.allRuns : null,
      );

    return (
      <ExperimentPage className="experiment-view-page" {...this.props}>
        <BestAssignmentModal
          experiment={experiment}
          ref={this._bestAssignmentModal}
        >
          {visitHistory}
        </BestAssignmentModal>
        <ObservationModal
          canEdit={false}
          experiment={experiment}
          ref={this._observationModal}
        >
          {visitHistory}
        </ObservationModal>
        {renderedStatusHeader}
        {this.props.isAiExperiment && (
          <div className="row">
            <Loading loading={!finishedLoadingRuns}>
              <DurationChart runs={this.state.allRuns} />
            </Loading>
          </div>
        )}
        {!allFailures && (
          <div className="row">
            <div className="top-row">
              {!isParetoOptimizedExperiment && (
                <>
                  <ExperimentSummary
                    bestAssignments={this.state.bestAssignments}
                    canEdit={this.props.canEdit}
                    experiment={experiment}
                    observations={observations}
                    onSelectBestAssignment={this.onSelectBestAssignment}
                  />
                  {ui.hasObservationsThatSatisfyThresholds(
                    this.props.experiment,
                    this.state.observations,
                  ) && (
                    <div className="charts top-cell">
                      <div className="chart-holder cell-content">
                        <ExperimentImprovement
                          experiment={experiment}
                          metric={_.first(ui.mostImportantMetrics(experiment))}
                          observations={observations}
                          onClickHandler={this.showObservationOnChartClick}
                          stoppingCriteria={this.state.stoppingCriteria}
                        />
                        <MoreGraphs experiment={experiment} />
                      </div>
                    </div>
                  )}
                </>
              )}
              {isParetoOptimizedExperiment && (
                <>
                  <ExperimentSummary
                    bestAssignments={this.state.bestAssignments}
                    canEdit={this.props.canEdit}
                    experiment={experiment}
                    observations={this.state.observations}
                    onSelectBestAssignment={this.onSelectBestAssignment}
                  />
                  <div className="charts top-cell">
                    <div className="chart-holder cell-content">
                      <div className="pareto-frontier-metric-chart">
                        <div className="title-label">
                          <Tooltip
                            html={true}
                            tooltip={
                              <div>
                                The points chosen for{" "}
                                <a
                                  href={`${DOCS_URL}/advanced_experimentation/multimetric_optimization`}
                                >
                                  best metrics
                                </a>{" "}
                                cannot improve in one metric without penalizing
                                the other. Click to explore the best points.
                              </div>
                            }
                          >
                            Best Metrics
                          </Tooltip>
                        </div>
                        <Loading
                          loading={!uniChartArgs}
                          empty={_.isEmpty(observations)}
                        >
                          {uniChartArgs && (
                            <UnifiedChart
                              args={uniChartArgs}
                              axisOptions={[AxisTypes.OPTIMIZED_METRIC]}
                              chartType={ChartTypes.Scatter2D}
                              hideAxisSelectors={true}
                              hideBestAssignmentsSelector={true}
                              hideChartTypeSelector={true}
                              hideFailures={true}
                              hideFailuresSelector={true}
                              hideFullCostObservations={true}
                              showMetricThresholds={true}
                              onClickHandler={this.showObservationOnChartClick}
                            />
                          )}
                        </Loading>
                      </div>
                      <MoreGraphs experiment={experiment} />
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
        {experiment.type !== ExperimentTypes.ONLINE && (
          <div className="row">
            <Loading
              loading={
                _.isEmpty(this.state.recentObservations) && !hasActiveRuns
              }
              empty={_.isEmpty(this.state.recentObservations) && !hasActiveRuns}
            >
              <div className="recent-data">
                <div className="recent-data-label">Active Runs</div>
                <RunsTable
                  columns={getRunColumns(this.props.experiment)}
                  enableCollapse={false}
                  promiseApiClient={this.services.promiseApiClient}
                  runs={this.state.activeRuns && this.state.activeRuns.data}
                />
                {!this.props.isAiExperiment &&
                  !_.isEmpty(this.state.recentObservations) && (
                    <>
                      <div className="recent-data-label">Recent Data</div>
                      <PollingHistoryTable
                        {...this.props}
                        experiment={experiment}
                        observations={sort_observations(
                          this.state.recentObservations,
                          false,
                        )}
                        onSelectObservation={(observation) =>
                          this._observationModal.current.show(observation)
                        }
                      />
                      <div className="paging-holder">
                        <a
                          className="paging-button btn btn-white-border"
                          href={ui.getExperimentUrl(experiment, "/history")}
                        >
                          See All
                        </a>
                      </div>
                    </>
                  )}
              </div>
            </Loading>
          </div>
        )}
      </ExperimentPage>
    );
  }
}

export default ExperimentViewPage;
