/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ModalForm from "../../../../component/modal/form";
import schemas from "../../../../react/schemas";
import {FooterTypes} from "../../../../component/modal/constant";
import {InviteRoles} from "../../../../user/roles";
import {PermissionsEditor} from "../permissions_editor/editor";
import {promiseFinally} from "../../../../utils";

export class CreateInviteAdminModal extends React.Component {
  static propTypes = {
    alertBroker: schemas.AlertBroker.isRequired,
    clientMap: PropTypes.objectOf(schemas.Client.isRequired).isRequired,
    onPermissionChange: PropTypes.func.isRequired,
    organization: schemas.Organization.isRequired,
    usedEmails: PropTypes.arrayOf(PropTypes.string.isRequired).isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      addingPermission: true,
      emails: this.props.usedEmails,
      editing: false,
      email: null,
      permissions: null,
      waiting: false,
    };
    this._modal = React.createRef();
  }

  onSubmit = (success, error) => {
    const email = this.state.email.toLowerCase();
    if (_.contains(this.state.emails, email)) {
      return error(
        `The email ${email} already exists in this organization.` +
          " Find their membership to make changes.",
      );
    } else {
      return this.setState({editing: true}, success);
    }
  };

  onPermissionChange = (clientId, email, newRole, oldRole) =>
    promiseFinally(
      this.props
        .onPermissionChange(clientId, email, newRole, oldRole)
        .then((newPermission) => {
          if (oldRole === InviteRoles.NO_ROLE) {
            this.props.alertBroker.info(
              `Invited to ${newPermission.client_name}.`,
            );
            this.setState((state) => ({
              emails: _.unique(state.emails.concat([email])),
            }));
          } else if (newPermission && newPermission.client) {
            this.props.alertBroker.info(
              `Updated invite for ${newPermission.client_name}.`,
            );
          } else {
            this.props.alertBroker.info("Removed team invite.");
            this.setState((state) => ({
              emails: _.without(state.emails, email),
            }));
          }
          return newPermission;
        }),
      () => this.setState({waiting: false}),
    );

  show = () => {
    this._modal.current.clearAlerts();
    this.setState(
      {
        addingPermission: true,
        editing: false,
        email: "",
        permissions: [],
        waiting: false,
      },
      () => this._modal.current.show(),
    );
  };

  render = () => {
    if (this.state.editing) {
      return (
        <ModalForm
          cancelButtonClass="btn btn-primary"
          cancelButtonLabel="Done"
          cancelDisabled={this.state.waiting || this.state.addingPermission}
          closeDelay={0}
          footer={FooterTypes.Cancel}
          hideOnSuccess={false}
          ref={this._modal}
          title={`Invite ${this.state.email} to teams in ${this.props.organization.name}`}
        >
          <PermissionsEditor
            addingPermission={this.state.addingPermission}
            alertBroker={this.props.alertBroker}
            allowDeleteLast={true}
            clientMap={this.props.clientMap}
            disableInput={this.state.waiting}
            email={this.state.email}
            onToggleAddingPermission={() =>
              this.setState((prevState) => ({
                addingPermission: !prevState.addingPermission,
              }))
            }
            onPermissionChange={this.onPermissionChange}
            permissions={this.state.permissions}
            showConfirm={true}
            updatePermissions={(permissions) => this.setState({permissions})}
          />
        </ModalForm>
      );
    } else {
      return (
        <ModalForm
          closeDelay={0}
          error={(msg) => this.props.alertBroker.show(msg, "danger")}
          footer={FooterTypes.SubmitAndCancel}
          onSubmit={this.onSubmit}
          hideOnSuccess={false}
          ref={this._modal}
          submitButtonLabel="Continue"
          title={`Invite someone to teams in ${this.props.organization.name}`}
        >
          <div className="email-input form-group">
            <label className="control-label">Email Address</label>
            <input
              className="form-control email"
              onChange={(e) => this.setState({email: e.target.value})}
              placeholder="user@domain.com"
              type="email"
              value={this.state.email || ""}
            />
          </div>
        </ModalForm>
      );
    }
  };
}
