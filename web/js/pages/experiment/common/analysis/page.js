/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/analysis.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Component from "../../../../react/component";
import ExperimentImprovement from "../../../../react_chart/experiment_improvement/component";
import ExperimentPage from "../../page_wrapper";
import ImportanceTable from "../../../../parameter/importance_table";
import Loading from "../../../../component/loading";
import ObservationModal from "../../../../experiment/observation_modal";
import ParallelCoordinatesWrapper from "../../../../react_chart/parallel_coordinates/wrapper";
import Tooltip from "../../../../component/tooltip";
import findClickedObservation from "../../../../experiment/find_clicked_observation.js";
import schemas from "../../../../react/schemas";
import ui from "../../../../experiment/ui";
import {AxisOrder, ChartTypes} from "../../../../react_chart/unified_constants";
import {AxisTypes} from "../../../../chart/constants";
import {DOCS_URL} from "../../../../net/constant";
import {TaskDistribution} from "../../../../react_chart/task_distribution";
import {UnifiedChart} from "../../../../react_chart/unified_chart";
import {getUnifiedChartArgs} from "../../../../react_chart/unified_chart_args";
import {isDefinedAndNotNull} from "../../../../utils";

class AnalysisPage extends Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    isAiExperiment: PropTypes.bool.isRequired,
    metricImportances: PropTypes.arrayOf(schemas.MetricImportance),
    promiseApiClient: schemas.PromiseApiClient.isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      bestAssignments: null,
      observations: null,
      stoppingCriteria: null,
      runs: null,
    };
    this._observationModal = React.createRef();
  }

  componentDidMount() {
    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .observations()
      .exhaustivelyPage()
      .then((observations) => this.setState({observations}));

    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .bestAssignments()
      .exhaustivelyPage()
      .then((bestAssignments) => this.setState({bestAssignments}));

    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .stoppingCriteria()
      .fetch()
      .then((stoppingCriteria) => this.setState({stoppingCriteria}));

    if (this.props.isAiExperiment) {
      this.props.promiseApiClient
        .clients(this.props.experiment.client)
        .projects(this.props.experiment.project)
        .trainingRuns()
        .exhaustivelyPage({
          filters: JSON.stringify([
            {
              operator: "==",
              field: "experiment",
              value: this.props.experiment.id,
            },
          ]),
        })
        .then((runs) => this.setState({runs}));
    }
  }

  showObservationModalOnChartClick = (data) => {
    const o = findClickedObservation(data, this.state.observations);
    if (this.props.isAiExperiment) {
      ui.navigateToRunForObservation(this.services, o.experiment, o.id, true);
    } else {
      this._observationModal.current.show(o);
    }
  };

  render() {
    const mostImportantMetrics = ui.mostImportantMetrics(this.props.experiment);

    const finishedLoadingRuns = this.props.isAiExperiment
      ? isDefinedAndNotNull(this.state.runs)
      : true;

    const uniChartArgs =
      this.props.experiment &&
      this.state.observations &&
      this.state.bestAssignments &&
      finishedLoadingRuns &&
      getUnifiedChartArgs(
        this.props.experiment,
        this.state.observations,
        this.state.bestAssignments,
        this.props.isAiExperiment ? this.state.runs : null,
      );
    const isParetoOptimizedExperiment = ui.isParetoOptimizedExperiment(
      this.props.experiment,
    );
    const isMultitask = isDefinedAndNotNull(this.props.experiment.tasks);
    const anyMetricMostImportantParamName =
      _.chain(this.props.metricImportances)
        .filter((i) => i.metric === _.first(mostImportantMetrics).name)
        .pluck("importances")
        .first()
        .pairs()
        .max(([, v]) => v)
        .first()
        .value() ||
      _.chain(this.props.experiment.parameters).pluck("name").first().value();
    const showBestParameters =
      _.size(this.props.experiment.parameters) +
        _.size(ui.storedMetrics(this.props.experiment)) >
      1;
    return (
      <div>
        <ObservationModal
          canEdit={false}
          experiment={this.props.experiment}
          ref={this._observationModal}
        />
        {isParetoOptimizedExperiment && (
          <>
            <div className="row">
              <div className="table-row">
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
                          cannot improve in one metric without penalizing the
                          other.
                        </div>
                      }
                    >
                      Best Metrics
                    </Tooltip>
                  </div>
                  <Loading
                    loading={!uniChartArgs}
                    empty={_.isEmpty(this.state.observations)}
                  >
                    {uniChartArgs && (
                      <div style={{textAlign: "center"}}>
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
                          onClickHandler={this.showObservationModalOnChartClick}
                        />
                        <span>Click to explore the best points.</span>
                      </div>
                    )}
                  </Loading>
                </div>
                {showBestParameters && (
                  <div className="pareto-frontier-parameter-chart">
                    <div className="title-label">Best Parameters</div>
                    <Loading
                      loading={!uniChartArgs}
                      empty={_.isEmpty(this.state.observations)}
                    >
                      {uniChartArgs && (
                        <UnifiedChart
                          args={uniChartArgs}
                          axisOptions={[
                            AxisTypes.PARAMETER,
                            AxisTypes.OPTIMIZED_METRIC,
                            AxisTypes.CONSTRAINED_METRIC,
                            AxisTypes.STORED_METRIC,
                            AxisTypes.METADATA,
                          ]}
                          chartType={ChartTypes.Scatter2D}
                          hideBestAssignmentsSelector={true}
                          hideChartTypeSelector={true}
                          hideFailures={true}
                          hideFailuresSelector={true}
                          hideFullCostObservations={true}
                          onClickHandler={this.showObservationModalOnChartClick}
                        />
                      )}
                    </Loading>
                  </div>
                )}
              </div>
            </div>
            <div className="row">
              <div className="table-row">
                {_.map(mostImportantMetrics, (m) => (
                  <div key={m.name} className="history-chart">
                    <div className="title-label">Experiment History</div>
                    <Loading
                      loading={!uniChartArgs}
                      empty={_.isEmpty(this.state.observations)}
                    >
                      {uniChartArgs && (
                        <UnifiedChart
                          args={uniChartArgs}
                          axisOptions={[
                            AxisTypes.PARAMETER,
                            AxisTypes.OPTIMIZED_METRIC,
                            AxisTypes.CONSTRAINED_METRIC,
                            AxisTypes.STORED_METRIC,
                            AxisTypes.METADATA,
                          ]}
                          chartType={ChartTypes.Scatter2D}
                          hideBestAssignmentsSelector={true}
                          hideChartTypeSelector={true}
                          hideFailures={true}
                          hideFailuresSelector={true}
                          hideFullCostObservations={
                            !_.has(this.props.experiment, "tasks")
                          }
                          onClickHandler={this.showObservationModalOnChartClick}
                          showMetricThresholds={ui.thresholdsAllowedForExperiment(
                            this.props.experiment,
                          )}
                          xAxisDefault={{
                            key: anyMetricMostImportantParamName,
                            label: anyMetricMostImportantParamName,
                            type: AxisTypes.PARAMETER,
                          }}
                          yAxisDefault={{
                            key: m.name,
                            label: m.name,
                            type: AxisTypes.OPTIMIZED_METRIC,
                          }}
                        />
                      )}
                    </Loading>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
        {!isParetoOptimizedExperiment && (
          <div className="row">
            <div className="table-row">
              <ExperimentImprovement
                experiment={this.props.experiment}
                metric={_.first(mostImportantMetrics)}
                observations={this.state.observations}
                onClickHandler={this.showObservationModalOnChartClick}
                stoppingCriteria={this.state.stoppingCriteria}
              />
              <div className="history-chart">
                <div className="title-label">Experiment History</div>
                <Loading
                  loading={!uniChartArgs}
                  empty={_.isEmpty(this.state.observations)}
                >
                  {uniChartArgs && (
                    <UnifiedChart
                      args={uniChartArgs}
                      axisOptions={[
                        AxisTypes.OPTIMIZED_METRIC,
                        AxisTypes.PARAMETER,
                        AxisTypes.CONSTRAINED_METRIC,
                        AxisTypes.STORED_METRIC,
                        AxisTypes.METADATA,
                      ]}
                      chartType={ChartTypes.Scatter2D}
                      hideBestAssignments={true}
                      hideBestAssignmentsSelector={true}
                      hideChartTypeSelector={true}
                      hideFailures={true}
                      hideFailuresSelector={true}
                      hideFullCostObservations={!isMultitask}
                      onClickHandler={this.showObservationModalOnChartClick}
                      showMetricThresholds={ui.thresholdsAllowedForExperiment(
                        this.props.experiment,
                      )}
                      showLegend={isMultitask}
                      xAxisDefault={{
                        key: anyMetricMostImportantParamName,
                        label: anyMetricMostImportantParamName,
                        type: AxisTypes.PARAMETER,
                      }}
                      yAxisOptions={AxisOrder.METRICS_FIRST}
                    />
                  )}
                </Loading>
              </div>
            </div>
          </div>
        )}
        <div className="row">
          <div className="table-row">
            <div className="importance-table">
              <div className="title-label">
                <Tooltip
                  tooltip={`
                      Parameter importance represents the predicted complexity of the objective
                      response relative to perturbations on this parameter. The minimum number of observations
                      necessary to calculate importance values is 5x the number of parameters.
                      Only shown for optimized metrics.
                    `}
                >
                  Parameter Importance
                </Tooltip>
              </div>
              <Loading
                empty={_.isEmpty(this.props.metricImportances)}
                emptyMessage={
                  _.isEmpty(this.props.experiment.conditionals) ? (
                    <p>
                      {
                        "You have insufficient data to calculate parameter importances."
                      }
                    </p>
                  ) : (
                    <p>
                      {
                        "Experiments with conditionals do not currently support parameter importances."
                      }
                    </p>
                  )
                }
              >
                <ImportanceTable
                  experiment={this.props.experiment}
                  metricImportances={this.props.metricImportances || []}
                />
              </Loading>
            </div>
            <div className="history-chart-4d">
              <div className="title-label">Full Experiment History</div>
              <Loading
                loading={!uniChartArgs}
                empty={_.isEmpty(this.state.observations)}
              >
                {uniChartArgs && (
                  <UnifiedChart
                    args={uniChartArgs}
                    chartType={ChartTypes.Scatter3DWithHighlight}
                    hideBestAssignments={true}
                    hideBestAssignmentsSelector={true}
                    hideChartTypeSelector={true}
                    hideFailures={true}
                    hideFailuresSelector={true}
                    hideFullCostObservations={
                      !_.has(this.props.experiment, "tasks")
                    }
                    highlightAxisOptions={[
                      AxisTypes.OPTIMIZED_METRIC,
                      AxisTypes.CONSTRAINED_METRIC,
                      AxisTypes.STORED_METRIC,
                    ]}
                    onClickHandler={this.showObservationModalOnChartClick}
                    zAxisOptions={AxisOrder.METRICS_FIRST}
                  />
                )}
              </Loading>
            </div>
          </div>
        </div>
        {isMultitask && (
          <div className="row">
            <div className="table-row">
              <div className="task-distribution">
                <div className="title-label">Task Distribution</div>
                <Loading
                  loading={!isDefinedAndNotNull(this.state.observations)}
                  empty={_.isEmpty(this.state.observations)}
                >
                  <TaskDistribution
                    experiment={this.props.experiment}
                    observations={this.state.observations || []}
                  />
                </Loading>
              </div>
            </div>
          </div>
        )}
        <div className="row">
          <div className="table-row">
            <div className="parcoords-chart">
              <div className="title-label">
                <Tooltip
                  tooltip={`
                      Parallel coordinates graph metrics, parameters and metadata on multiple vertical axes.
                      Axes can be rearranged by dragging their label.
                      Each axis can also be filtered by clicking and dragging vertically along the axis.
                      `}
                >
                  Parallel Coordinates
                </Tooltip>
              </div>
              <Loading
                loading={!uniChartArgs}
                empty={_.isEmpty(this.state.observations)}
              >
                {uniChartArgs && (
                  <ParallelCoordinatesWrapper
                    args={uniChartArgs}
                    metricImportances={this.props.metricImportances}
                  />
                )}
                {!_.isEmpty(this.props.experiment.conditionals) && (
                  <div className="parcoord-chart controls">
                    <span>
                      This experiment has conditionals. Please be sure to select
                      a{" "}
                      <a
                        href={`${DOCS_URL}/intro/main-concepts/parameter_space#define-conditional-parameters`}
                      >
                        satisfied
                      </a>{" "}
                      subset of the parameters.
                    </span>
                  </div>
                )}
              </Loading>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default function ExperimentAnalysisPage(props) {
  return (
    <ExperimentPage className="experiment-analysis-page" {...props}>
      <AnalysisPage {...props} />
    </ExperimentPage>
  );
}
