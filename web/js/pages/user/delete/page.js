/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/user.less";

import _ from "underscore";
import React from "react";

import NetError from "../../../alert/error";
import Page from "../../../component/page";

const CONFIRM_DELETE_TEXT = "DELETE MY ACCOUNT";

export default class extends React.Component {
  static displayName = "UserDeletePage";

  shouldSend = () => {
    return (
      !this.props.externalAuthorizationEnabled ||
      this._passwordInput.value === CONFIRM_DELETE_TEXT
    );
  };

  onSubmit = (e) => {
    e.preventDefault();
    if (this.shouldSend()) {
      this.props.promiseApiClient
        .users(this.props.loginState.userId)
        .delete({password: this._passwordInput.value})
        .catch(this.props.alertBroker.errorHandlerThatExpectsStatus(400, 403))
        .then(() => this.props.navigator.navigateTo("/"));
    } else {
      throw new NetError({
        message: "Must enter password or confirmation text",
        status: 400,
      });
    }
  };

  render() {
    const label = this.props.externalAuthorizationEnabled
      ? `Enter '${CONFIRM_DELETE_TEXT}' without quotes to Confirm`
      : "Enter Password to Confirm";
    const inputType = this.props.externalAuthorizationEnabled
      ? "text"
      : "password";
    return (
      <Page loggedIn={true} title="Delete Account">
        {!_.isEmpty(this.props.userPermissions) && (
          <div className="alert alert-info">
            You may need to delete the following teams before proceeding:
            <ul>
              {_.map(this.props.userPermissions, (permission) => (
                <li key={permission.client.id}>
                  <a href={`/client/${permission.client.id}/delete`}>
                    Delete {permission.client.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
        <p>
          Once you delete your account, there is no going back. Are you
          absolutely sure you want to delete your account?
        </p>
        <form onSubmit={(e) => this.onSubmit(e)}>
          <div className="form-group">
            <label className="control-label">{label}</label>
            <input
              className="form-control"
              ref={(c) => {
                this._passwordInput = c;
              }}
              type={inputType}
            />
            <p>
              If you do not have a password, you can use{" "}
              <a href="/forgot_password">Forgot Password</a> to create a
              password.
            </p>
          </div>
          <input
            type="submit"
            className="btn btn-danger"
            value="Delete my account"
          />
        </form>
      </Page>
    );
  }
}
