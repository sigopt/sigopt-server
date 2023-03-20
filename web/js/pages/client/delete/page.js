/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import Form from "../../../component/form";
import Page from "../../../component/page";

export default class extends React.Component {
  static displayName = "ClientDeletePage";

  render() {
    const canDelete =
      this.props.clientPermission && this.props.clientPermission.can_admin;
    return (
      <Page loggedIn={true} title={`Delete Team - ${this.props.client.name}`}>
        <div>
          <p>
            {canDelete
              ? "Deleting a team will prevent reporting any new data." +
                " Once you delete a team, there is no going back." +
                ` Are you absolutely sure you want to delete ${this.props.client.name}?`
              : "You do not have permission to delete this team"}
          </p>
          {canDelete && (
            <Form csrfToken={this.props.loginState.csrfToken}>
              <input
                type="submit"
                className="btn btn-danger"
                value={`Delete ${this.props.client.name}`}
              />
            </Form>
          )}
        </div>
      </Page>
    );
  }
}
