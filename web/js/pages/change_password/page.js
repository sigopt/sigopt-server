/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/change_password.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import createReactClass from "create-react-class";

import Form from "../../component/form";
import NetError from "../../alert/error";
import NewPasswordInput from "../../user/password";
import Page from "../../component/page";
import Spinner from "../../component/spinner";
import SubmittableMixin from "../../mixins/submittable";
import schemas from "../../react/schemas";

export default createReactClass({
  displayName: "ChangePasswordPage",
  propTypes: {
    alertBroker: schemas.AlertBroker.isRequired,
    code: PropTypes.string,
    continueHref: PropTypes.string,
    email: PropTypes.string,
    loginState: schemas.LoginState.isRequired,
    navigator: schemas.Navigator.isRequired,
    promiseApiClient: schemas.PromiseApiClient.isRequired,
    required: PropTypes.bool.isRequired,
    sessionUpdater: schemas.SessionUpdater.isRequired,
    user: schemas.User,
  },

  mixins: [SubmittableMixin],

  getInitialState: function () {
    return {
      oldPassword: "",
      newPassword: "",
      verifyPassword: "",
    };
  },

  changePassword: function () {
    if (this.state.newPassword === this.state.verifyPassword) {
      return this.props.promiseApiClient.sessions().update({
        email: this.getEmail(),
        password_reset_code: this.props.code,
        old_password: this.state.oldPassword,
        new_password: this.state.newPassword,
      });
    } else {
      return Promise.reject(
        new NetError({
          message: "Passwords must match.",
          status: 400,
        }),
      );
    }
  },

  onSubmit: function () {
    this.submit(
      (s, e) =>
        this.changePassword()
          .then((session) => this.props.sessionUpdater.setSession(session))
          .then(s, e),
      () => {
        this.props.alertBroker.show("Password changed.", "success");
        this.setState(this.getInitialState());
        this.props.navigator.navigateTo(
          this.props.continueHref || "/user/info",
        );
      },
      this.props.alertBroker.errorHandlerThatExpectsStatus(400, 401, 403),
    );
  },

  getEmail: function () {
    const providedEmail = this.props.email;
    const userEmail = this.props.user && this.props.user.email;
    return providedEmail || userEmail;
  },

  render: function () {
    const providedEmail = this.props.email;
    const userEmail = this.props.user && this.props.user.email;
    if (providedEmail && userEmail && providedEmail !== userEmail) {
      return (
        <p>
          Looks like you followed a link that was not meant for you. Try logging
          out and visiting the link again.
        </p>
      );
    }

    const email = this.getEmail();
    /* eslint-disable react/jsx-no-bind */
    const pageBody = (
      <div>
        <div>
          {this.props.required ? (
            <p>You must update your password before proceeding.</p>
          ) : null}
          <Form
            className="change-password-form"
            csrfToken={this.props.loginState.csrfToken}
            error={this.props.alertBroker.errorHandlerThatExpectsStatus(400)}
            onSubmit={_.bind(this.onSubmit, this)}
          >
            {email ? <input type="hidden" value={email} /> : null}
            {!this.props.code && (
              <div className="form-group">
                <label className="control-label">Current Password</label>
                <input
                  name="old-password"
                  onChange={(e) => this.setState({oldPassword: e.target.value})}
                  value={this.state.oldPassword || ""}
                  type="password"
                  className="form-control"
                />
              </div>
            )}
            <NewPasswordInput
              onPasswordUpdate={(newPassword) => this.setState({newPassword})}
              onVerifyPasswordUpdate={(verifyPassword) =>
                this.setState({verifyPassword})
              }
              password={this.state.newPassword || ""}
              change={true}
              verify={true}
              verifyPassword={this.state.verifyPassword || ""}
            />
            {this.props.code ? (
              <input type="hidden" value={this.props.code} />
            ) : null}
            {this.state.submitting ? <Spinner /> : null}
            {!this.state.submitting && (
              <div className="form-group">
                <input
                  type="submit"
                  className="btn btn-primary"
                  value="Update"
                />
              </div>
            )}
          </Form>
        </div>
        <div>
          <p className="invalidate-notice">
            For your protection, this will log you out of all other browsers,
            and reset all API tokens associated with your account.
          </p>
        </div>
      </div>
    );
    /* eslint-enable react/jsx-no-bind */

    return (
      <Page title="Change Password" className="change-password-page">
        {pageBody}
      </Page>
    );
  },
});
