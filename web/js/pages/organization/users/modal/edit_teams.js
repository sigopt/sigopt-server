/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ModalForm from "../../../../component/modal/form";
import schemas from "../../../../react/schemas";
import {FooterTypes} from "../../../../component/modal/constant";
import {InviteRoles} from "../../../../user/roles";
import {PermissionsEditor} from "../permissions_editor/editor";
import {getInviteRoleDisplayText} from "../../../../user/helpers";
import {promiseFinally} from "../../../../utils";

const EditTeamsContent = (props) => (
  <span>
    {props.isCurrentUser ? (
      <p>You are not allowed to edit your own membership.</p>
    ) : null}
    <PermissionsEditor
      addingPermission={props.addingPermission}
      alertBroker={props.alertBroker}
      clientMap={props.clientMap}
      disableInput={props.waiting || props.isCurrentUser}
      email={props.email}
      onToggleAddingPermission={props.onToggleAddingPermission}
      onPermissionChange={props.onPermissionChange}
      permissions={props.permissions}
      showConfirm={true}
      updatePermissions={props.updatePermissions}
    />
  </span>
);

export class EditTeamsModal extends React.Component {
  static propTypes = {
    alertBroker: schemas.AlertBroker.isRequired,
    clientMap: PropTypes.objectOf(schemas.Client).isRequired,
    currentUser: schemas.User.isRequired,
    onPermissionChange: PropTypes.func.isRequired,
    onUninvite: PropTypes.func.isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      addingPermission: false,
      editing: false,
      email: "",
      isCurrentUser: false,
      permissions: [],
      waiting: false,
    };
    this._modal = React.createRef();
  }

  open = (userRelation, editing) => {
    this.setState({
      addingPermission: false,
      editing,
      email: userRelation.email,
      isCurrentUser:
        Boolean(userRelation.membership) &&
        userRelation.membership.user.id === this.props.currentUser.id,
      permissions: _.values(userRelation.permissionMap),
      userRelation,
      waiting: false,
    });
    this._modal.current.clearAlerts();
    this._modal.current.show();
  };

  getEditTitle() {
    if (this.state.userRelation) {
      return this.state.userRelation.membership
        ? `Edit teams for ${this.state.userRelation.membership.user.name}`
        : `Edit invitation for ${this.state.userRelation.email}`;
    }
    return null;
  }

  getUninviteTitle() {
    if (this.state.userRelation) {
      return this.state.userRelation.membership
        ? `Remove ${this.state.userRelation.membership.user.name}`
        : `Uninvite ${this.state.userRelation.email}`;
    }
    return null;
  }

  onPermissionChange = (clientId, email, newRole, oldRole) =>
    promiseFinally(
      this.props
        .onPermissionChange(clientId, email, newRole, oldRole)
        .then((newPermission) => {
          const clientName = this.props.clientMap[clientId].name;
          if (oldRole === InviteRoles.NO_ROLE) {
            this.props.alertBroker.info(
              `Added to ${clientName} as ${getInviteRoleDisplayText(newRole)}.`,
            );
          } else if (newPermission && newPermission.client) {
            this.props.alertBroker.info(
              `Role for ${clientName} changed to ${getInviteRoleDisplayText(
                newRole,
              )}.`,
            );
          } else {
            this.props.alertBroker.info(`Removed from ${clientName}.`);
          }
          return newPermission;
        }),
      () => this.setState({waiting: false}),
    );

  onSubmitUninvite = (success, error) => {
    return this.props
      .onUninvite(this.state.email)
      .then(success)
      .catch((err) =>
        _.each(
          [
            this.props.alertBroker.errorHandlerThatExpectsStatus(400, 409),
            error,
          ],
          (f) => f(err),
        ),
      );
  };

  modalValidator = () => !(this.state.isCurrentUser || this.state.waiting);

  toggleAddPermission = () =>
    this.setState((prevState) => ({
      addingPermission: !prevState.addingPermission,
    }));

  updatePermissions = (permissions) => this.setState({permissions});

  render() {
    if (this.state.editing) {
      return (
        <ModalForm
          cancelButtonClass="btn btn-primary"
          cancelButtonLabel="Done"
          cancelDisabled={
            !this.state.isCurrentUser &&
            (this.state.waiting || this.state.addingPermission)
          }
          closeDelay={0}
          footer={FooterTypes.Cancel}
          ref={this._modal}
          title={this.getEditTitle()}
          validator={this.modalValidator}
        >
          <EditTeamsContent
            addingPermission={this.state.addingPermission}
            alertBroker={this.props.alertBroker}
            clientMap={this.props.clientMap}
            email={this.state.email}
            isCurrentUser={this.state.isCurrentUser}
            onToggleAddingPermission={this.toggleAddPermission}
            onPermissionChange={this.onPermissionChange}
            permissions={this.state.permissions}
            updatePermissions={this.updatePermissions}
            waiting={this.state.waiting}
          />
        </ModalForm>
      );
    } else {
      let modalContent = <div />;
      if (this.state.userRelation) {
        if (this.state.userRelation.membership) {
          modalContent = (
            <>
              <p>
                Would you like to remove{" "}
                <b>{this.state.userRelation.membership.user.name}</b> from this
                organization?
              </p>
              <p>
                They will be removed from the organization completely - if you
                would like to change their role on a single team, try editing
                their membership.
              </p>
            </>
          );
        } else {
          modalContent = (
            <>
              <p>
                Would you like to uninvite{" "}
                <b>{this.state.userRelation.email}</b>?
              </p>
              <p>
                They will be uninvited from the organization completely - if you
                would like to change their role on a single team, try editing
                their invitation.
              </p>
            </>
          );
        }
      }
      return (
        <ModalForm
          cancelButtonLabel="Cancel"
          closeDelay={2000}
          footer={FooterTypes.SubmitAndCancel}
          onSubmit={this.onSubmitUninvite}
          ref={this._modal}
          submitButtonClass="btn btn-danger"
          submitButtonLabel={
            this.state.userRelation && this.state.userRelation.membership
              ? "Remove from Organization"
              : "Uninvite"
          }
          title={this.getUninviteTitle()}
        >
          {modalContent}
        </ModalForm>
      );
    }
  }
}
