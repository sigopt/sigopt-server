/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/home.less";
import "./page.less";

import _ from "underscore";
import React from "react";
import date from "date-and-time";

import ChevronRightGlyph from "../../component/glyph/chevron-right";
import ClockGlyph from "../../component/glyph/clock";
import Component from "../../react/component";
import FlaskGlyph from "../../component/glyph/flask";
import FolderGlyph from "../../component/glyph/folder";
import ForwardGlyph from "../../component/glyph/forward";
import LearnMore from "./components/learn_more";
import Loading from "../../component/loading";
import Page from "../../component/page";
import Welcome from "./components/welcome";
import {CompactExperimentProgress} from "../../experiment/progress";
import {DOCS_URL} from "../../net/constant";
import {
  RECENT_EXPERIMENT,
  RECENT_PROJECT,
  RECENT_RUN,
} from "./get_recent_activity";
import {isUndefinedOrNull} from "../../utils";

const glyphMap = {
  [RECENT_EXPERIMENT]: <FlaskGlyph />,
  [RECENT_PROJECT]: <FolderGlyph />,
  [RECENT_RUN]: <ForwardGlyph />,
};

const renderActivityTime = (time) => {
  const now = new Date();
  const activityDate = new Date(time * 1000);
  const sameYear = now.getFullYear() === activityDate.getFullYear();
  if (!sameYear) {
    return date.format(activityDate, "MMM D YYYY");
  }
  const sameMonthAndDate =
    now.getMonth() === activityDate.getMonth() &&
    now.getDate() === activityDate.getDate();
  if (!sameMonthAndDate) {
    return date.format(activityDate, "MMMM D");
  }
  return date.format(activityDate, "h:mm A");
};

const ExperimentProgressInfo = ({recentActivity}) => {
  return (
    <CompactExperimentProgress experiment={recentActivity.extra.experiment} />
  );
};

class ProjectInfo extends Component {
  state = {count: null};

  componentDidMount() {
    this.componentDidUpdate();
  }

  componentDidUpdate() {
    const projectId = this.props.recentActivity.extra.projectId;
    const project = this.props.projects[projectId];
    if (!this.loading && project) {
      this.loading = true;
      this.services.promiseApiClient
        .clients(project.client)
        .projects(project.id)
        .aiexperiments()
        .fetch({limit: 0})
        .then(({count}) => this.setState({count}));
    }
  }

  render() {
    return (
      <Loading loading={isUndefinedOrNull(this.state.count)}>
        {this.state.count} Experiments
      </Loading>
    );
  }
}

const RunStateInfo = ({recentActivity}) => {
  return {
    active: "Active",
    completed: "Completed",
    failed: "Failed",
  }[recentActivity.extra.state];
};

const ExtraInfo = (props) => {
  const InfoComponent = {
    [RECENT_EXPERIMENT]: ExperimentProgressInfo,
    [RECENT_PROJECT]: ProjectInfo,
    [RECENT_RUN]: RunStateInfo,
  }[props.recentActivity.type];
  return <InfoComponent {...props} />;
};

const ProjectLink = ({projects, projectId}) => {
  const project = projects[projectId];
  return (
    <a
      className="project-link"
      href={`/client/${project.client}/project/${project.id}`}
    >
      {project.name}
    </a>
  );
};

const RecentActivityRow = ({recentActivity, projects}) => (
  <tr className="recent-activity-item" key={recentActivity.href}>
    <td className="icon">{glyphMap[recentActivity.type]}</td>
    <td className="text">
      <span className="title">
        <a href={recentActivity.href}>{recentActivity.name}</a>
      </span>
      <br />
      <span className="caption">
        {recentActivity.classTitle} Created
        {recentActivity.inProject ? (
          <>
            {" "}
            in{" "}
            <ProjectLink
              projects={projects}
              projectId={recentActivity.inProject}
            />
          </>
        ) : null}
      </span>
    </td>
    <td className="time">
      <a className="cell-link" href={recentActivity.href}>
        <ClockGlyph /> {renderActivityTime(recentActivity.time)}
      </a>
    </td>
    <td className="extra">
      <a className="cell-link" href={recentActivity.href}>
        <ExtraInfo projects={projects} recentActivity={recentActivity} />
      </a>
    </td>
    <td className="arrow">
      <a className="cell-link" href={recentActivity.href}>
        <ChevronRightGlyph />
      </a>
    </td>
  </tr>
);

export default class HomePage extends Component {
  static displayName = "HomePage";

  constructor(props, context) {
    super(props, context);
    this.state = {
      showWelcome: this.props.currentUser.show_welcome,
    };
    this._modal = React.createRef();
  }

  hideWelcome = () => {
    this.setState(
      {
        showWelcome: false,
      },
      () => {
        this.props.promiseApiClient
          .users(this.props.currentUser.id)
          .update({showWelcome: false});
      },
    );
  };

  componentDidMount() {
    if (this._modal.current) {
      this._modal.current.show();
    }
  }

  nullContent(forRuns) {
    const link = forRuns
      ? `${DOCS_URL}/ai-module-api-references/tutorial/run`
      : `${DOCS_URL}/ai-module-api-references/tutorial/experiment`;
    return (
      <p>
        0 runs &mdash;{" "}
        <i>
          learn to{" "}
          <a href={link}>Create {forRuns ? "a Run" : "an Experiment"}</a>
        </i>
      </p>
    );
  }

  render() {
    const pageTitle = "Home";
    return (
      <Page loggedIn={true} title={pageTitle} className="home experiment-list">
        {this.props.currentUser && this.state.showWelcome ? (
          <Welcome
            hide={this.hideWelcome}
            showRunsContent={this.props.showRunsContent}
          />
        ) : null}
        <h2>Recent Activity</h2>
        {_.isEmpty(this.props.recentActivity) ? (
          <div className="recent-activity">
            <p>You haven&apos;t shared any information with SigOpt yet.</p>
            <p>
              Learn more about how SigOpt can streamline your intelligent
              experimentation process using the links below.
            </p>
          </div>
        ) : (
          <table className="recent-activity">
            <tbody>
              {_.map(this.props.recentActivity, (recentActivity) => (
                <RecentActivityRow
                  key={recentActivity.href}
                  projects={this.props.clientProjects}
                  recentActivity={recentActivity}
                />
              ))}
            </tbody>
          </table>
        )}
        <LearnMore />
      </Page>
    );
  }
}
