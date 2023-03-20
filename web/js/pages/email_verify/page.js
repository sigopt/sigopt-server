/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import Component from "../../react/component";
import Page from "../../component/page";
import ResendVerificationEmailButton from "../../user/resend";

export default class extends Component {
  static displayName = "EmailVerifyPage";

  state = {error: null};

  errorBlock = () => (
    <div>
      {this.state.error && (
        <div>
          <p>Oops, looks like we couldn&rsquo;t verify your email.</p>
        </div>
      )}
      <ResendVerificationEmailButton
        email={this.props.email}
        loginState={this.props.loginState}
        promiseApiClient={this.props.promiseApiClient}
      />
    </div>
  );

  componentDidMount() {
    this.props.promiseApiClient
      .sessions()
      .create({
        code: this.props.code,
        email: this.props.email,
      })
      .then((session) => this.props.sessionUpdater.setSession(session))
      .then(() => this.props.navigator.navigateTo("/setup"))
      .catch((err) => {
        this.setState({error: err});
      });
  }

  render() {
    return (
      <Page title="Verify Email">
        <div>
          {this.props.code && !this.state.error
            ? "Loading..."
            : this.errorBlock()}
        </div>
      </Page>
    );
  }
}
