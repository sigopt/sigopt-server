/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import PropTypes from "prop-types";
import React from "react";

import ModalForm from "../component/modal/form";
import schemas from "../react/schemas";
import ui from "../experiment/ui";
import {FooterTypes} from "../component/modal/constant";

class DeleteTokenModal extends React.Component {
  static propTypes = {
    experiment: schemas.Experiment,
    loginState: schemas.LoginState.isRequired,
    promiseApiClient: schemas.PromiseApiClient.isRequired,
    success: PropTypes.func,
    token: schemas.Token.isRequired,
  };

  show = () => {
    this._modal.show();
  };

  onSubmit = (success, error) =>
    this.props.promiseApiClient
      .tokens(this.props.token.token)
      .delete()
      .then(success, error);

  render() {
    const experiment = this.props.experiment;

    const experimentLink =
      experiment && experiment.name ? (
        <a href={ui.getExperimentUrl(experiment)}>{experiment.name}</a>
      ) : (
        <a href={`/experiment/${this.props.token.experiment}`}>
          experiment {this.props.token.experiment}
        </a>
      );

    return (
      <ModalForm
        className="delete-form"
        csrfToken={this.props.loginState.csrfToken}
        footer={FooterTypes.SubmitAndCancel}
        onSubmit={this.onSubmit}
        ref={(c) => (this._modal = c)}
        submitButtonClass="btn btn-danger confirm-delete-btn"
        submitButtonLabel="Delete"
        success={() => this.props.success && this.props.success()}
        title="Delete Guest Token"
      >
        <p>
          Are you sure you want to delete this token? People you have shared the
          guest link with will no longer have access to {experimentLink}.
        </p>
      </ModalForm>
    );
  }
}

export default DeleteTokenModal;
