/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import PropTypes from "prop-types";
import React from "react";

import Spinner from "../../../../component/spinner";
import XmarkGlyph from "../../../../component/glyph/xmark";
import schemas from "../../../../react/schemas";
import {InviteRoles} from "../../../../user/roles";
import {RolesDropdown} from "../helper";

export class EditPermissionRow extends React.Component {
  static propTypes = {
    clientName: PropTypes.string.isRequired,
    disableInput: PropTypes.bool.isRequired,
    onPermissionChange: PropTypes.func.isRequired,
    permission: schemas.PendingPermission.isRequired,
  };

  state = {
    selectedRole: this.props.permission.role,
  };

  updatePermission(role) {
    const oldRole = this.state.selectedRole;
    if (role !== oldRole) {
      this.setState({modifying: true, selectedRole: role}, () =>
        this.props
          .onPermissionChange(
            this.props.permission.client,
            this.props.permission.email,
            role,
            oldRole,
          )
          .then(() => this.setState({modifying: false}))
          .catch(() =>
            this.setState({modifying: false, selectedRole: oldRole}),
          ),
      );
    }
  }

  deletePermission() {
    this.setState({modifying: true}, () =>
      this.props
        .onPermissionChange(
          this.props.permission.client,
          this.props.permission.email,
          InviteRoles.NO_ROLE,
          this.state.selectedRole,
        )
        .catch({modifying: false}),
    );
  }

  render() {
    return (
      <tr
        className="edit-permission-row"
        data-id={this.props.permission.client}
      >
        <td className="table-client-cell">{this.props.clientName}</td>
        <td className="table-role-cell">
          <RolesDropdown
            selectedRole={this.state.selectedRole}
            disabled={this.props.disableInput}
            onSelectRole={(role) => this.updatePermission(role)}
          />
        </td>
        <td className="table-buttons-cell">
          {this.state.modifying ? (
            <Spinner position="absolute" size={10} />
          ) : (
            <a
              className="delete-button btn btn-xs btn-remove btn-spacing"
              disabled={this.props.disableInput}
              onClick={() => this.props.disableInput || this.deletePermission()}
            >
              <XmarkGlyph />
            </a>
          )}
        </td>
      </tr>
    );
  }
}
