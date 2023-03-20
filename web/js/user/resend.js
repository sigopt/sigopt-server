/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import React from "react";

import ActionButton from "../component/action_button";

class ResendVerificationEmailButton extends React.Component {
  state = {
    email: this.props.email || "",
  };

  actionRef = React.createRef();

  success = () => {
    setTimeout(() => this.actionRef.current.props.resetSubmissionState(), 2000);
  };

  render() {
    const userId = this.props.loginState && this.props.loginState.userId;
    const showInput = !userId && !this.props.email;
    return (
      <div>
        {showInput && (
          <input
            className="form-control"
            onChange={(e) => this.setState({email: e.target.value})}
            type="email"
            value={this.state.email}
          />
        )}
        <ActionButton
          disabled={!userId && !this.state.email}
          ref={this.actionRef}
          onClick={
            userId
              ? () =>
                  this.props.promiseApiClient
                    .users(userId)
                    .verifications()
                    .create()
              : () =>
                  this.props.promiseApiClient
                    .verifications()
                    .create({email: this.state.email})
          }
          size={this.props.size}
          success={this.success}
        >
          Resend verification email
        </ActionButton>
      </div>
    );
  }
}

export default ResendVerificationEmailButton;
