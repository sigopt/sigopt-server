/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import createReactClass from "create-react-class";

import Form from "../../component/form";
import NetError from "../../alert/error";
import Page from "../../component/page";
import Spinner from "../../component/spinner";
import SubmittableMixin from "../../mixins/submittable";
import schemas from "../../react/schemas";
import {validateEmail} from "../../net/email";

const ResetPasswordForm = createReactClass({
  displayName: "ResetPasswordForm",

  propTypes: {
    alertBroker: PropTypes.object.isRequired,
    legacyApiClient: schemas.LegacyApiClient.isRequired,
    loginState: schemas.LoginState.isRequired,
  },

  mixins: [SubmittableMixin],

  getInitialState: function () {
    return {
      email: "",
    };
  },

  onSubmit: function () {
    this.props.alertBroker.clearAlerts();

    // The input field, with type 'email' also adds
    // some small level of validation.
    if (!validateEmail(this.state.email)) {
      return this.props.alertBroker.handle(
        new NetError({
          message: "Please enter a valid email address.",
          status: 400,
        }),
      );
    }

    this.submit(
      _.partial(this.props.legacyApiClient.forgotPassword, {
        email: this.state.email,
      }),
      () =>
        this.props.alertBroker.show(
          `If the email ${this.state.email} exists in our system, we will send a link to reset your password.
         If you do not receive the password reset email within a few minutes,
         please check your spam folder or contact your account administrator.`,
          "info",
        ),
      this.props.alertBroker.errorHandlerThatExpectsStatus(400),
    );
    return null;
  },

  render: function () {
    if (this.state.submitting) {
      return <Spinner />;
    }

    return (
      <Form
        className="form-horizontal"
        onSubmit={this.onSubmit}
        csrfToken={this.props.loginState.csrfToken}
      >
        <div className="form-group">
          <div className="col-sm-12">
            <label htmlFor="email" className="col-sm-4 control-label">
              Email
            </label>
            <div className="col-sm-6">
              <input
                className="form-control"
                onChange={(e) => this.setState({email: e.target.value})}
                placeholder="Email"
                type="email"
                value={this.state.email}
              />
            </div>
          </div>
          <div className="col-sm-12">
            <div className="col-sm-offset-4 col-sm-6">
              <input type="submit" className="btn btn-primary" value="Reset" />
            </div>
          </div>
        </div>
      </Form>
    );
  },
});

class ForgotPasswordPage extends React.Component {
  static propTypes = {
    canReset: PropTypes.bool.isRequired,
  };

  render() {
    return (
      <Page title="Forgot Password">
        {this.props.canReset ? <ResetPasswordForm {...this.props} /> : null}
        {!this.props.canReset && (
          <p>
            Your administrator has not enabled password reset. Please contact
            them to reset your password.
          </p>
        )}
      </Page>
    );
  }
}

export default ForgotPasswordPage;
