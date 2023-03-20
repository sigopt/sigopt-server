/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Tooltip from "../../../../component/tooltip";
import schemas from "../../../../react/schemas";
import {EditPermissionRow} from "./edit_row";
import {InviteRoles} from "../../../../user/roles";
import {NewPermissionRow} from "./new_row";

export class PermissionsEditor extends React.Component {
  static propTypes = {
    addingPermission: PropTypes.bool.isRequired,
    alertBroker: schemas.AlertBroker.isRequired,
    clientMap: PropTypes.objectOf(schemas.Client.isRequired).isRequired,
    disableInput: PropTypes.bool.isRequired,
    email: PropTypes.string.isRequired,
    onPermissionChange: PropTypes.func.isRequired,
    onToggleAddingPermission: PropTypes.func.isRequired,
    permissions: PropTypes.arrayOf(schemas.PendingPermission.isRequired),
    showConfirm: PropTypes.bool.isRequired,
    updatePermissions: PropTypes.func.isRequired,
  };

  onPermissionChange(...args) {
    return this.props.onPermissionChange(...args).catch((err) => {
      this.props.alertBroker.errorHandlerThatExpectsStatus(400, 403, 409)(err);
      return Promise.reject(err);
    });
  }

  addPermission = (clientId, role) => {
    return this.onPermissionChange(
      clientId,
      this.props.email,
      role,
      InviteRoles.NO_ROLE,
    ).then((newPermission) => {
      this.props.updatePermissions(
        this.props.permissions.concat([newPermission]),
      );
      this.props.onToggleAddingPermission();
    });
  };

  handlePermissionChange = (clientId, email, newRole, oldRole) => {
    return this.onPermissionChange(clientId, email, newRole, oldRole).then(
      (newPermission) => {
        if (newRole === InviteRoles.NO_ROLE) {
          this.props.updatePermissions(
            _.filter(
              this.props.permissions,
              (p) => !(p.client === clientId && p.email === email),
            ),
          );
        } else if (oldRole === InviteRoles.NO_ROLE) {
          this.props.updatePermissions(
            this.props.permissions.concat([newPermission]),
          );
        } else {
          this.props.updatePermissions(
            _.map(this.props.permissions, (oldPermission) =>
              oldPermission.client === newPermission.client
                ? newPermission
                : oldPermission,
            ),
          );
        }
        return newPermission;
      },
    );
  };

  render() {
    const tooltipContent = (
      <span>
        <b>Read</b> users can view but cannot modify or make experiments.{" "}
        <b>Write</b> users can view, make, and modify experiments. <b>Admin</b>{" "}
        users can view, make, and modify experiments as well as invite other
        users to the team.
      </span>
    );
    return (
      <table className="permission-editor table table-condensed">
        <thead>
          <tr>
            <th className="table-name-header">Team</th>
            <th className="table-role-header">
              <Tooltip html={true} tooltip={tooltipContent}>
                Role
              </Tooltip>
            </th>
            <th className="table-buttons-header" />
          </tr>
        </thead>
        <tbody>
          {_.map(this.props.permissions, (permission) => {
            const client = this.props.clientMap[permission.client];
            return (
              client && (
                <EditPermissionRow
                  clientName={client.name}
                  disableInput={this.props.disableInput}
                  key={permission.client}
                  onPermissionChange={this.handlePermissionChange}
                  permission={permission}
                />
              )
            );
          })}
          {this.props.addingPermission && (
            <NewPermissionRow
              clientMap={this.props.clientMap}
              disableInput={this.props.disableInput}
              onCancel={this.props.onToggleAddingPermission}
              onPermissionChosen={this.addPermission}
              permissions={this.props.permissions}
              showConfirm={this.props.showConfirm}
            />
          )}
          {!this.props.addingPermission &&
            !this.props.disableInput &&
            _.size(this.props.permissions) < _.size(this.props.clientMap) && (
              <tr className="add-team-row">
                <td colSpan="3">
                  <a
                    className="add-client-button btn btn-sm btn-primary"
                    disabled={this.props.disableInput}
                    onClick={() =>
                      this.props.disableInput ||
                      this.props.onToggleAddingPermission()
                    }
                  >
                    {_.isEmpty(this.props.permissions)
                      ? "Add to Team"
                      : "Add to another Team"}
                  </a>
                </td>
              </tr>
            )}
        </tbody>
      </table>
    );
  }
}
