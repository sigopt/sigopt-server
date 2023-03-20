/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/properties.less";

/* eslint-disable react/jsx-no-bind */
import PropTypes from "prop-types";
import React from "react";

import Component from "../../../../react/component";
import DuplicateButton from "../../../../experiment/buttons/duplicate_button";
import ExperimentEditor from "../../../../experiment/editor";
import ExperimentPage from "../../page_wrapper";
import ModalForm from "../../../../component/modal/form";
import Tooltip from "../../../../component/tooltip";
import refreshPage from "../../../../net/refresh";
import schemas from "../../../../react/schemas";
import ui from "../../../../experiment/ui";

class ArchiveExperimentModal extends Component {
  state = {includeRuns: false};

  _modal = React.createRef();

  promptArchive = () => this._modal.current.show();

  hide = () => this._modal.current.hide();

  toggleIncludeRuns = () =>
    this.setState(({includeRuns}) => ({includeRuns: !includeRuns}));

  archiveExperiment = () => {
    const route = this.props.isAiExperiment
      ? this.services.promiseApiClient.aiexperiments
      : this.services.promiseApiClient.experiments;

    route(this.props.experiment.id)
      .delete({include_runs: this.state.includeRuns ? "true" : "false"})
      .then(refreshPage);
  };

  render() {
    return (
      <ModalForm ref={this._modal} title="Archive Experiment">
        <div className="archive-experiment-modal">
          <div>Are you sure you want to archive your experiment?</div>
          <div className="checkbox">
            <label className="control-label">
              <input
                className="toggle-runs"
                type="checkbox"
                value={this.state.includeRuns}
                onChange={this.toggleIncludeRuns}
              />{" "}
              Archive runs as well
            </label>
          </div>
          <div>
            <a
              className="archive btn btn-danger"
              onClick={this.archiveExperiment}
            >
              Archive
            </a>{" "}
            <a className="cancel btn btn-warning" onClick={this.hide}>
              Cancel
            </a>
          </div>
        </div>
      </ModalForm>
    );
  }
}

export default class extends React.Component {
  static displayName = "ExperimentPropertiesPage";

  static propTypes = {
    alertBroker: schemas.AlertBroker.isRequired,
    canEdit: PropTypes.bool,
    clientId: PropTypes.string,
    creator: schemas.User,
    currentProject: schemas.Project,
    experiment: schemas.Experiment.isRequired,
    isAiExperiment: PropTypes.bool.isRequired,
    isGuest: PropTypes.bool.isRequired,
    legacyApiClient: schemas.LegacyApiClient.isRequired,
    loginState: schemas.LoginState.isRequired,
    promiseApiClient: schemas.PromiseApiClient.isRequired,
  };

  state = {
    experiment: this.props.experiment,
  };

  _archiveModal = React.createRef();

  archiveExperiment = () => this._archiveModal.current.promptArchive();

  render() {
    return (
      <ExperimentPage
        {...this.props}
        experiment={this.state.experiment}
        className="experiment-properties-page"
      >
        <ArchiveExperimentModal
          ref={this._archiveModal}
          experiment={this.state.experiment}
        />
        <ExperimentEditor
          alertBroker={this.props.alertBroker}
          canEdit={this.props.canEdit}
          clientId={this.props.clientId}
          currentProject={this.props.currentProject}
          create={false}
          creator={this.props.creator}
          experiment={this.state.experiment}
          loginState={this.props.loginState}
          onSuccess={(experiment) => this.setState({experiment: experiment})}
          promiseApiClient={this.props.promiseApiClient}
          renderAlerts={false}
        />
        <div className="danger-zone">
          <a
            className="btn btn-secondary btn-md"
            href={ui.getExperimentUrl(this.props.experiment, "/api")}
          >
            <Tooltip tooltip="Generate code to recreate this experiment in your preferred programming language">
              Generate as Code
            </Tooltip>
          </a>
          {!this.props.isAiExperiment &&
            !this.props.isGuest &&
            this.props.canEdit && (
              <span>
                <DuplicateButton
                  alertBroker={this.props.alertBroker}
                  className="btn btn-secondary btn-md"
                  experiment={this.state.experiment}
                  loginState={this.props.loginState}
                />
              </span>
            )}
          {this.props.canEdit && (
            <a className="btn btn-danger" onClick={this.archiveExperiment}>
              Archive Experiment
            </a>
          )}
        </div>
      </ExperimentPage>
    );
  }
}
