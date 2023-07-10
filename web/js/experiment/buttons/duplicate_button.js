/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Form from "../../component/form";
import Modal from "../../component/modal/base";
import TriggerModalButton from "../../component/modal/button";
import schemas from "../../react/schemas";
import ui from "../../experiment/ui";

export default class DuplicateButton extends React.Component {
  static propTypes = {
    alertBroker: schemas.AlertBroker.isRequired,
    className: PropTypes.string,
    experiment: schemas.Experiment.isRequired,
    loginState: schemas.LoginState.isRequired,
  };

  state = {
    includeObservations: false,
  };

  title = () =>
    this.props.experiment.development
      ? "Copy to Production"
      : "Duplicate Experiment";

  toggleIncludeObservations = () => {
    this.setState((prevState) => ({
      includeObservations: !prevState.includeObservations,
    }));
  };

  renderModalBody = () => (
    <Form
      action={`/experiment/${this.props.experiment.id}/copy`}
      csrfToken={this.props.loginState.csrfToken}
      method="post"
    >
      {this.props.experiment.development ? (
        <div>
          Experiments copied to production will be fully-featured and will count
          against your billing quota. Suggestions will not be copied.
        </div>
      ) : null}
      {!this.props.experiment.development && (
        <p>Create a copy of this experiment.</p>
      )}
      {ui.isAiExperiment(this.props.experiment) ? null : (
        <div className="checkbox">
          <label className="control-label">
            <input
              type="checkbox"
              name="include_observations"
              onChange={this.toggleIncludeObservations}
              checked={this.state.includeObservations}
            />{" "}
            Also copy this experiment&rsquo;s observation data.
          </label>
        </div>
      )}
      <button className="btn btn-primary" type="submit">
        {this.title()}
      </button>
    </Form>
  );

  render() {
    return (
      <TriggerModalButton className={this.props.className} label={this.title()}>
        <Modal
          alertBroker={this.props.alertBroker}
          ref={(c) => (this._duplicateModal = c)}
          className="duplicate-modal"
          title={this.title()}
        >
          {this.renderModalBody()}
        </Modal>
      </TriggerModalButton>
    );
  }
}
