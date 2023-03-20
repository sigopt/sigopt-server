/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import CheckGlyph from "../../../../component/glyph/check";
import ClientsDropdown from "../../../../client/dropdown";
import Spinner from "../../../../component/spinner";
import XmarkGlyph from "../../../../component/glyph/xmark";
import schemas from "../../../../react/schemas";
import {InviteRoles} from "../../../../user/roles";
import {RolesDropdown} from "../helper";

export class NewPermissionRow extends React.Component {
  static propTypes = {
    clientMap: PropTypes.objectOf(schemas.Client.isRequired).isRequired,
    disableInput: PropTypes.bool.isRequired,
    onCancel: PropTypes.func.isRequired,
    onPermissionChosen: PropTypes.func.isRequired,
    permissions: PropTypes.arrayOf(PropTypes.object.isRequired).isRequired,
    showConfirm: PropTypes.bool.isRequired,
  };

  state = {
    selectedClientId: _.first(this.getAvailableClients()),
    selectedRole: InviteRoles.USER,
    waiting: false,
  };

  getAvailableClients() {
    const usedClients = _.chain(this.props.permissions)
      .pluck("client")
      .map((c) => [c, true])
      .object()
      .value();
    return _.chain(this.props.clientMap)
      .filter((c) => !usedClients[c.id])
      .sortBy((c) => c.name)
      .value();
  }

  getSelectedClient() {
    const availableClients = this.getAvailableClients();
    if (this.state.selectedClientId) {
      const selected = _.find(
        availableClients,
        (c) => c.id === this.state.selectedClientId,
      );
      if (selected) {
        return selected;
      }
    }
    return _.first(availableClients);
  }

  getSelectedClientId() {
    const selectedClient = this.getSelectedClient();
    if (selectedClient) {
      return selectedClient.id;
    }
    return null;
  }

  getSelectedClientName() {
    const selectedClient = this.getSelectedClient();
    if (selectedClient) {
      return selectedClient.name;
    }
    return null;
  }

  finished() {
    this.setState({waiting: true});
    this.props
      .onPermissionChosen(this.getSelectedClientId(), this.state.selectedRole)
      .catch(() => this.setState({waiting: false}));
  }

  render() {
    return (
      <tr className="add-permission-row">
        <td className="table-client-cell">
          <ClientsDropdown
            allowBlank={false}
            buttonClassName="btn btn-sm btn-white-border dropdown-toggle"
            clients={this.getAvailableClients()}
            onClientSelect={(client) =>
              this.setState({selectedClientId: client.id})
            }
            selectedClient={this.getSelectedClient()}
          />
        </td>
        <td className="table-role-cell">
          <RolesDropdown
            selectedRole={this.state.selectedRole}
            disabled={this.state.waiting}
            onSelectRole={(role) => this.setState({selectedRole: role})}
          />
        </td>
        <td className="table-buttons-cell">
          {this.state.waiting ? (
            <Spinner position="absolute" size={10} />
          ) : (
            <div>
              <a
                className={classNames(
                  "accept-button",
                  "btn",
                  this.props.showConfirm || "btn-xs",
                  "btn-remove",
                  "btn-spacing",
                  this.props.showConfirm && "confirm",
                )}
                disabled={this.props.disableInput}
                onClick={() => this.props.disableInput || this.finished()}
              >
                {this.props.showConfirm ? "Confirm" : <CheckGlyph />}
              </a>
              <a
                className="cancel-button btn btn-xs btn-remove btn-spacing"
                disabled={this.props.disableInput}
                onClick={() => this.props.disableInput || this.props.onCancel()}
              >
                <XmarkGlyph />
              </a>
            </div>
          )}
        </td>
      </tr>
    );
  }
}
