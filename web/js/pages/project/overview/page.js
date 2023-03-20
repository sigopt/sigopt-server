/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/project_page.less";

import _ from "underscore";
import React from "react";

import Component from "../../../react/component";
import GetStartedContent from "../../../project/get_started";
import Loading from "../../../component/loading";
import ProjectPage from "../page_wrapper";
import RecentActivity from "./recent_activity";
import Section from "../../../component/section";
import SourcePool from "../../../net/pool";
import TableMagnitude from "./table_magnitude";
import TrainingRunHistograms from "../../../training_run/histograms";
import promiseComponent from "../../../component/promise_component";
import {
  AsynchronousUserDataSource,
  AvailableUserDataSource,
} from "../../../user/data_source";
import {isUndefinedOrNull} from "../../../utils";
import {unarchivedRunsFilter} from "../../../training_run/constants";

const HistogramsContent = promiseComponent(
  ({project, services}) =>
    services.promiseApiClient
      .clients(project.client)
      .projects(project.id)
      .trainingRuns()
      .exhaustivelyPage({
        filters: JSON.stringify([unarchivedRunsFilter]),
      }),
  ({data, focusedResource, metrics}) => {
    if (_.isEmpty(data)) {
      return null;
    }
    const runs = data;
    let focusedRuns = [];
    if (focusedResource) {
      if (focusedResource.object === "experiment") {
        focusedRuns = _.filter(
          runs,
          (run) => run.experiment === focusedResource.id,
        );
      } else {
        focusedRuns = _.filter(runs, (run) => run.id === focusedResource.id);
      }
    }
    return (
      <TrainingRunHistograms
        focusedRuns={focusedRuns}
        metrics={metrics}
        runs={runs}
      />
    );
  },
);

class BestResultsContent extends Component {
  state = {experiments: null, focusedResource: null};

  componentDidMount() {
    this.fetchAllAiExperiments();
  }

  componentWillUnmount() {
    this.unmounted = false;
  }

  fetchAllAiExperiments = () =>
    this.services.promiseApiClient
      .clients(this.props.project.client)
      .projects(this.props.project.id)
      .aiexperiments()
      .exhaustivelyPage()
      .then((experiments) => this.unmounted || this.setState({experiments}));

  onResourceFocus = (focusedResource) => this.setState({focusedResource});

  render() {
    const {metrics, project} = this.props;
    const {focusedResource} = this.state;
    const loading = isUndefinedOrNull(this.state.experiments);
    return (
      <>
        <Loading loading={loading}>
          {!loading && (
            <TableMagnitude
              experiments={this.state.experiments}
              focusedResource={focusedResource}
              metrics={metrics}
              onResourceFocus={this.onResourceFocus}
              project={project}
            />
          )}
        </Loading>
        {!_.isEmpty(metrics) && this.props.runCount > 1 && (
          <HistogramsContent
            focusedResource={focusedResource}
            metrics={metrics}
            project={project}
            services={this.services}
          />
        )}
      </>
    );
  }
}

const TopSection = promiseComponent(
  ({project, services}) =>
    services.promiseApiClient
      .clients(project.client)
      .projects(project.id)
      .trainingRuns()
      .fetch({limit: 0})
      .then(({count}) => Promise.resolve(count)),
  (props) => {
    const runCount = props.data;
    let className, content, title;
    if (runCount === 0) {
      title = "Get Started";
      content = <GetStartedContent />;
      className = "getstarted-section";
    } else {
      title = "Best Results";
      content = <BestResultsContent {...props} runCount={runCount} />;
      className = "bestresults-section";
    }
    return (
      <Section className={className} fullWidth={true} title={title}>
        {content}
      </Section>
    );
  },
);

export default class ProjectOverviewPage extends Component {
  constructor(props) {
    super(props);
    this.userDataSources = new SourcePool((key) =>
      key === this.props.currentUser.id
        ? new AvailableUserDataSource(key, this.props)
        : new AsynchronousUserDataSource(key, this.props),
    );
  }

  state = {};

  render() {
    const {recentActions} = this.props;
    return (
      <ProjectPage {...this.props}>
        <TopSection {...this.props} services={this.services} />
        <Section fullWidth={true} title="Recent Activity">
          <RecentActivity
            actions={recentActions}
            userDataSources={this.userDataSources}
          />
        </Section>
      </ProjectPage>
    );
  }
}
