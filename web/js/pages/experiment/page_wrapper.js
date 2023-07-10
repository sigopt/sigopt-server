/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import ClockGlyph from "../../component/glyph/clock";
import Component from "../../react/component";
import ExperimentTitle from "../../experiment/experiment_title";
import FileGlyph from "../../component/glyph/file";
import HardDriveGlyph from "../../component/glyph/hard-drive";
import InboxGlyph from "../../component/glyph/inbox";
import PencilGlyph from "../../component/glyph/pencil";
import ScrewdriverWrench from "../../component/glyph/screwdriver-wrench";
import ShareButton from "./common/view/share_button";
import SignalGlyph from "../../component/glyph/signal";
import TabLink from "../../component/tab_link";
import UndeleteButton from "../../component/delete_button/undelete_button";
import schemas from "../../react/schemas";
import ui from "../../experiment/ui";
import {DOCS_URL, PRODUCTION_WEB_URL} from "../../net/constant";
import {ExperimentStates, ExperimentTypes} from "../../experiment/constants";

class ExperimentPage extends Component {
  constructor(...args) {
    super(...args);
    this.state = {
      failedRuns: 0,
      currExperiment: this.props.experiment,
    };
  }
  static propTypes = {
    canEdit: PropTypes.bool.isRequired,
    canShare: PropTypes.bool.isRequired,
    children: PropTypes.node,
    className: PropTypes.string,
    experiment: schemas.Experiment.isRequired,
    isAiExperiment: PropTypes.bool,
    isGettingStarted: PropTypes.bool,
    isGuest: PropTypes.bool.isRequired,
    path: PropTypes.string.isRequired,
    promiseApiClient: schemas.PromiseApiClient.isRequired,
    user: schemas.User,
  };

  unarchiveExperiment = () =>
    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .update({state: "active"});

  updateExperimentPage = () => {
    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .fetch()
      .then((data) => {
        this.setState({
          currExperiment: data,
        });
      });

    if (this.props.isAiExperiment) {
      this.updateTrainingRuns();
    }
  };

  updateTrainingRuns = () => {
    const runFilters = JSON.stringify([
      {
        field: "experiment",
        operator: "==",
        value: this.props.experiment.id,
      },
      {
        field: "state",
        operator: "==",
        value: "failed",
      },
    ]);

    this.props.promiseApiClient
      .clients(this.props.experiment.client)
      .projects(this.props.experiment.project)
      .trainingRuns()
      .fetch({
        filters: runFilters,
        limit: 0,
      })
      .then((data) => {
        this.setState({
          failedRuns: data.count,
        });
      });
  };

  componentDidMount() {
    this.updateExperimentPage();
    this.interval = setInterval(this.updateExperimentPage, 30000);
  }

  componentWilllUnmount() {
    clearInterval(this.interval);
  }

  render() {
    const experiment = this.state.currExperiment;
    const isGuest = !this.props.user;
    const isGettingStarted = this.props.isGettingStarted;
    const deleted = experiment.state === ExperimentStates.DELETED;
    const experimentPath = ui.getExperimentUrl(experiment);
    const shareButton = (
      <ShareButton
        name="Share"
        experiment={experiment}
        promiseApiClient={this.services.promiseApiClient}
      />
    );
    const navLinks = (
      <nav className="experiment-nav">
        <TabLink
          glyph={<FileGlyph />}
          href={experimentPath}
          path={this.props.path}
        >
          Summary
        </TabLink>
        <TabLink
          glyph={<SignalGlyph />}
          href={`${experimentPath}/analysis`}
          path={this.props.path}
        >
          Analysis
        </TabLink>
        {!deleted && !this.props.isAiExperiment && (
          <TabLink
            glyph={<InboxGlyph />}
            href={`${experimentPath}/suggestions`}
            path={this.props.path}
          >
            Suggestions
          </TabLink>
        )}
        {!deleted && this.props.isAiExperiment ? (
          <TabLink
            glyph={<InboxGlyph />}
            href={`${experimentPath}/inform`}
            path={this.props.path}
          >
            Inform the Optimizer
          </TabLink>
        ) : null}
        <TabLink
          glyph={<ClockGlyph />}
          href={`${experimentPath}/history`}
          path={this.props.path}
        >
          History
        </TabLink>
        {!deleted &&
        !isGuest &&
        this.props.canEdit &&
        !this.props.isAiExperiment ? (
          <TabLink
            glyph={<HardDriveGlyph />}
            href={`${experimentPath}/report`}
            path={this.props.path}
          >
            Add Data
          </TabLink>
        ) : null}
        <TabLink
          glyph={<PencilGlyph />}
          href={`${experimentPath}/properties`}
          path={this.props.path}
        >
          Properties
        </TabLink>
        <TabLink
          href={`${experimentPath}/admin`}
          glyph={<ScrewdriverWrench />}
          path={this.props.path}
        >
          Experiment Admin
        </TabLink>
      </nav>
    );

    const breadcrumbs = [];
    if (!this.props.isGuest) {
      if (ui.isAiExperiment(this.props.experiment)) {
        breadcrumbs.push({
          href: "/projects",
          label: "Projects",
        });
        breadcrumbs.push({
          href: `/client/${this.props.experiment.client}/project/${this.props.experiment.project}`,
          label: this.props.experiment.project,
        });
        breadcrumbs.push({
          href: `/client/${this.props.experiment.client}/project/${this.props.experiment.project}/aiexperiments`,
          label: "AI Experiments",
        });
      } else {
        breadcrumbs.push({
          href: "/experiments",
          label: "Experiments",
        });
      }
    }

    return (
      <div className={classNames("experiment-page", this.props.className)}>
        {isGettingStarted ? (
          <section className="getting-started-intro">
            <h2>Welcome!</h2>
            <p>
              This is your newly created experiment! You can follow along and
              watch as new data comes in. You can also use these pages to
              monitor how your experiment is doing. If you&rsquo;d like to
              create your own experiment,{" "}
              <a href={`${PRODUCTION_WEB_URL}/try-it`}>contact us</a> for a
              trial.
            </p>
          </section>
        ) : null}
        <ExperimentTitle
          gradientStyle="experiment"
          info={
            <>
              <dt>Experiment ID</dt>
              <dd>{this.props.experiment.id}</dd>
            </>
          }
          title={experiment.name}
          breadcrumbs={breadcrumbs}
          experiment={experiment}
          secondaryButtons={
            !this.props.isGuest && this.props.canShare ? shareButton : null
          }
          promiseApiClient={this.props.promiseApiClient}
          failedRuns={this.state.failedRuns}
        >
          {navLinks}
        </ExperimentTitle>
        {/* TODO(SN-1164): Make this a PageBody, will require some css tweaks */}
        <section className="page-body">
          <div className="container-fluid">
            <div className="row">
              <div className="experiment-info">
                {experiment.development ? (
                  <div className="development-alert">
                    <div className="row">
                      <div className="alert-description">
                        This experiment has been created in{" "}
                        <a
                          href={`${DOCS_URL}/core-module-api-references/api-topics/api-tokens-and-authentication#development-mode`}
                        >
                          development mode
                        </a>
                        {""}.
                      </div>
                    </div>
                  </div>
                ) : null}
                {_.contains(
                  [ExperimentTypes.GRID, ExperimentTypes.RANDOM],
                  experiment.type,
                ) && (
                  <div className="grid-alert">
                    <div className="row">
                      <div className="alert-description">
                        This experiment will be optimized with {experiment.type}{" "}
                        search.{" "}
                        <a href={`/experiment/${experiment.id}/properties`}>
                          View properties
                        </a>
                      </div>
                    </div>
                  </div>
                )}
                {deleted ? (
                  <div className="deleted-alert">
                    <div className="row">
                      <div className="alert-description">
                        This experiment has been archived and can no longer be
                        modified.
                      </div>
                      <div className="undelete-button-holder">
                        <UndeleteButton
                          handleClick={this.unarchiveExperiment}
                        />
                      </div>
                    </div>
                  </div>
                ) : null}
                <div className="experiment-info-content">
                  {this.props.children}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    );
  }
}

export default ExperimentPage;
