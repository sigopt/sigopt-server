/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import ModalForm from "../component/modal/form";
import schemas from "../react/schemas";
import {FooterTypes} from "../component/modal/constant";

class RotateTokenModal extends React.Component {
  static propTypes = {
    children: PropTypes.node.isRequired,
    loginState: schemas.LoginState.isRequired,
    promiseApiClient: schemas.PromiseApiClient.isRequired,
    success: PropTypes.func.isRequired,
    token: schemas.Token,
  };

  show = () => {
    this._modal.show();
  };

  onSubmit = (success, error) =>
    this.props.promiseApiClient
      .tokens(this.props.token.token)
      .update({token: "rotate"})
      .then((result) => {
        this.props.success(result);
        success(result);
      }, error);

  render() {
    return (
      <ModalForm
        className="rotate-form"
        closeDelay={0}
        csrfToken={this.props.loginState.csrfToken}
        footer={FooterTypes.SubmitAndCancel}
        onSubmit={this.onSubmit}
        ref={(c) => (this._modal = c)}
        submitButtonClass="btn btn-danger confirm-rotate-btn"
        submitButtonLabel="Rotate"
        title="Rotate Token"
      >
        {this.props.children}
      </ModalForm>
    );
  }
}

export default RotateTokenModal;
