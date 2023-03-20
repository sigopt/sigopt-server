/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/training_run/view.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import stringify from "fast-json-stable-stringify";

import ArchiveButton from "../../../component/delete_button/delete_button";
import CodeSection from "./code";
import Component from "../../../react/component";
import DatasetSection from "./dataset";
import FeatureImportancesSection from "./feature_importances";
import FilesSection from "./files";
import InfoSection from "./info";
import Loading from "../../../component/loading";
import LogSection from "./log";
import MetadataSection from "./metadata";
import MetricSection from "./metric";
import MpmCheckpointsChart from "../../../chart/mpm_checkpoints_chart";
import OptimizationSection from "./optimization";
import ParameterSection from "./parameter";
import ReactChart from "../../../react_chart/react_chart";
import Section from "../../../component/section";
import TrainingRunHistograms from "../../../training_run/histograms";
import TrainingRunPage from "../page_wrapper";
import UndeleteButton from "../../../component/delete_button/undelete_button";
import schemas from "../../../react/schemas.js";
import {CodeBlock} from "../../../component/code_block";
import {isUndefinedOrNull} from "../../../utils";
import {unarchivedRunsFilter} from "../../../training_run/constants";

const CheckpointSection = ({checkpoints, trainingRun}) => {
  if (trainingRun.checkpoint_count === 0) {
    return null;
  }
  const loading = !checkpoints;
  const metricNames = _.chain(checkpoints)
    .pluck("values")
    .flatten()
    .pluck("name")
    .unique()
    .value();
  // NOTE: the padding approximately accounts for the height of the chart's x-axis title and tick labels
  const singlePlotHeightPx = 150;
  const paddingPx = 100;
  const style = {
    height: _.size(metricNames) * singlePlotHeightPx + paddingPx,
  };
  return (
    <Section fullWidth={true} title="Checkpoints">
      <div className="checkpoints-chart" style={style}>
        <Loading loading={loading}>
          {loading ? null : (
            <ReactChart
              args={{
                data: [
                  {
                    checkpointsByRunId: _.groupBy(checkpoints, "training_run"),
                    metricNames,
                    trainingRuns: [trainingRun],
                  },
                ],
              }}
              cls={MpmCheckpointsChart}
            />
          )}
        </Loading>
      </div>
    </Section>
  );
};

const traceLabels = {
  highlight: "This run",
};
class HistogramsSection extends Component {
  state = {};

  componentDidMount() {
    if (!_.isEmpty(this.metricNames)) {
      const {project} = this.props;
      this.services.promiseApiClient
        .clients(project.client)
        .projects(project.id)
        .trainingRuns()
        .exhaustivelyPage({
          filters: JSON.stringify([unarchivedRunsFilter]),
        })
        .then((runs) => _.filter(runs, (r) => !_.isEmpty(r.values)))
        .then((runs) => this.setState({runs}));
    }
  }

  get metricNames() {
    return _.keys(this.props.trainingRun.values);
  }

  render() {
    const metricNames = this.metricNames;
    if (_.isEmpty(metricNames)) {
      return null;
    } else {
      const {trainingRun} = this.props;
      const {runs} = this.state;
      return (
        <Section fullWidth={true} title="Performance">
          <p>
            View this run in the distribution of run metrics in this project.
          </p>
          <Loading
            empty={_.size(runs) < 2}
            emptyMessage={
              <p>
                Please check back later. There&apos;s not enough data yet to
                compare this run with other runs.
              </p>
            }
            loading={isUndefinedOrNull(runs)}
          >
            <TrainingRunHistograms
              focusedRuns={[trainingRun]}
              metrics={metricNames}
              runs={runs}
              traceLabels={traceLabels}
              showThisRun={true}
            />
          </Loading>
        </Section>
      );
    }
  }
}

export default class TrainingRunViewPage extends Component {
  static propTypes = {
    canEdit: PropTypes.bool,
    files: PropTypes.arrayOf(PropTypes.object),
    loginState: schemas.LoginState.isRequired,
    project: schemas.Project,
    promiseApiClient: schemas.PromiseApiClient.isRequired,
    showHistogram: PropTypes.bool,
    trainingRun: schemas.TrainingRun.isRequired,
    user: schemas.User,
  };

  state = {};

  componentDidMount() {
    this.services.promiseApiClient
      .trainingRuns(this.props.trainingRun.id)
      .checkpoints()
      .exhaustivelyPage()
      .then((reversedCheckpoints) =>
        this.setState({checkpoints: reversedCheckpoints.reverse()}),
      );
  }

  archiveRun = () =>
    this.props.promiseApiClient
      .trainingRuns(this.props.trainingRun.id)
      .delete();

  unArchiveRun = () =>
    this.props.promiseApiClient
      .trainingRuns(this.props.trainingRun.id)
      .update({deleted: false});

  render() {
    const run = this.props.trainingRun;
    return (
      <TrainingRunPage {...this.props}>
        {run.deleted && (
          <div className="alert alert-danger archived">
            <p className="alert-description">This run has been archived.</p>
            {this.props.canEdit && (
              <UndeleteButton handleClick={this.unArchiveRun} />
            )}
          </div>
        )}
        <div className="run-page-wrapper">
          <CheckpointSection
            checkpoints={this.state.checkpoints}
            trainingRun={this.props.trainingRun}
          />
          {this.props.showHistogram && this.props.project && (
            <HistogramsSection
              project={this.props.project}
              trainingRun={this.props.trainingRun}
            />
          )}
          <MetricSection trainingRun={run} />
          <InfoSection trainingRun={run} user={this.props.user} />
          <OptimizationSection trainingRun={run} />
          <ParameterSection trainingRun={run} />
          <MetadataSection trainingRun={run} />
          <DatasetSection trainingRun={run} />
          {run.sys_metadata && run.sys_metadata.feature_importances && (
            <FeatureImportancesSection trainingRun={run} />
          )}
          <FilesSection files={this.props.files} trainingRun={run} />
          <CodeSection trainingRun={run} />
          <LogSection trainingRun={run} />
          <Section title="API Object">
            <CodeBlock language="json">
              {stringify(run, {space: 2, terseEmptyLiterals: true})}
            </CodeBlock>
          </Section>
          {!run.deleted && this.props.canEdit && (
            <Section fullWidth={true} title="Actions">
              <ArchiveButton
                label="Archive Run"
                handleClick={this.archiveRun}
              />
            </Section>
          )}
        </div>
      </TrainingRunPage>
    );
  }
}
