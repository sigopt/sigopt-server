/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import AsynchronousUserName from "../../user/name_span";
import Component from "../../react/component";
import FieldEditor from "../../component/fieldeditor";
import NoteStickyGlyph from "../../component/glyph/note-sticky";
import PageBody from "../../component/page_body";
import PageTitle from "../../component/page_title";
import ProjectCodeModal from "./components/project_code_modal";
import SourcePool from "../../net/pool";
import TabLink from "../../component/tab_link";
import TriggerModalButton from "../../component/modal/button";
import schemas from "../../react/schemas";
import {
  AsynchronousUserDataSource,
  AvailableUserDataSource,
} from "../../user/data_source";

const ArchiveProjectButton = ({deleted, onArchive, onUnarchive}) => (
  <a
    className={classNames("archive-btn", "btn-inverse", {unarchive: deleted})}
    onClick={deleted ? onUnarchive : onArchive}
  >
    {deleted ? "Unarchive" : "Archive"}
  </a>
);

export default class ProjectPage extends Component {
  static propTypes = {
    alertBroker: schemas.AlertBroker.isRequired,
    apiToken: PropTypes.string.isRequired,
    children: PropTypes.node,
    currentUser: schemas.User,
    loginState: schemas.LoginState.isRequired,
    path: PropTypes.string.isRequired,
    project: schemas.Project.isRequired,
    promiseApiClient: schemas.PromiseApiClient.isRequired,
  };

  constructor(props) {
    super(props);
    this.userDataSources = new SourcePool((key) =>
      key === this.props.currentUser.id
        ? new AvailableUserDataSource(key, this.props)
        : new AsynchronousUserDataSource(key, this.props),
    );
  }

  state = {deleted: this.props.project.deleted};

  updateName = (id, val, s, e) => {
    this.props.promiseApiClient
      .clients(this.props.project.client)
      .projects(id)
      .update({name: val.name})
      .then(s, e);
  };

  archiveProject = () => {
    this.services.promiseApiClient
      .clients(this.props.project.client)
      .projects(this.props.project.id)
      .update({deleted: true})
      .then(() => this.setState({deleted: true}));
  };

  unarchiveProject = () => {
    this.services.promiseApiClient
      .clients(this.props.project.client)
      .projects(this.props.project.id)
      .update({deleted: false})
      .then(() => this.setState({deleted: false}));
  };

  render() {
    const projectPath = `/client/${this.props.project.client}/project/${this.props.project.id}`;
    const navLinks = (
      <nav className="experiment-nav">
        <TabLink href={`${projectPath}/overview`} path={this.props.path}>
          Overview
        </TabLink>
        <TabLink href={`${projectPath}/aiexperiments`} path={this.props.path}>
          AI Experiments
        </TabLink>
        <TabLink href={`${projectPath}/runs`} path={this.props.path}>
          Runs
        </TabLink>
        <TabLink href={`${projectPath}/analysis`} path={this.props.path}>
          Analysis
        </TabLink>
        <TabLink
          glyph={<NoteStickyGlyph />}
          href={`${projectPath}/notes`}
          path={this.props.path}
        >
          Notes
        </TabLink>
      </nav>
    );

    return (
      <div className="project-page">
        <PageTitle
          gradientStyle="project"
          info={
            <>
              <dt>Project ID</dt>
              <dd data-field-name="project-id">{this.props.project.id}</dd>
              {this.props.project.user && (
                <>
                  <dt>Created By</dt>
                  <dd>
                    <AsynchronousUserName
                      dataSource={this.userDataSources.get(
                        this.props.project.user,
                      )}
                    />
                  </dd>
                </>
              )}
            </>
          }
          breadcrumbs={[{href: "/projects", label: "AI Projects"}]}
          secondaryButtons={
            <>
              <TriggerModalButton
                className="btn-inverse"
                label={<span>Create Experiment Code</span>}
              >
                <ProjectCodeModal
                  apiToken={this.props.apiToken}
                  project={this.props.project}
                  projectId={this.props.project.id}
                />
              </TriggerModalButton>
              <ArchiveProjectButton
                deleted={this.state.deleted}
                onArchive={this.archiveProject}
                onUnarchive={this.unarchiveProject}
              />
            </>
          }
          title={
            <div data-field-name="project-name">
              <FieldEditor
                alertBroker={this.props.alertBroker}
                fieldName="name"
                loginState={this.props.loginState}
                object={this.props.project}
                buttonClassOverride="editable-page-title"
                updateFunction={this.updateName}
              />
            </div>
          }
        >
          {navLinks}
        </PageTitle>
        <PageBody>
          {this.state.deleted && (
            <div className="alert alert-danger">
              This project has been archived and will no longer be shown in your
              recent projects.
            </div>
          )}
          {this.props.children}
        </PageBody>
      </div>
    );
  }
}
