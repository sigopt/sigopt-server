/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import Page from "../../../component/page";

export default class extends React.Component {
  static displayName = "ClientCreatePage";

  onSubmit = (e) => {
    e.preventDefault();
    this.props.promiseApiClient
      .clients()
      .create({name: this._nameInput.value})
      .then((client) =>
        this.props.sessionUpdater.setApiToken(
          this.props.loginState.apiToken,
          client.id,
        ),
      )
      .then(
        () => this.props.navigator.navigateTo("/tokens/info"),
        this.props.alertBroker.errorHandlerThatExpectsStatus(400, 403),
      );
  };

  render() {
    return (
      <Page title="Create Team" loggedIn={true}>
        <form className="form" onSubmit={this.onSubmit}>
          <div className="form-group client-name-input">
            <label className="control-label">Team Name</label>
            <input
              ref={(c) => {
                this._nameInput = c;
              }}
              type="text"
              className="form-control"
              placeholder="Team Name"
            />
          </div>
          <div className="form-group">
            <input type="submit" className="btn btn-primary" value="Create" />
          </div>
        </form>
      </Page>
    );
  }
}
