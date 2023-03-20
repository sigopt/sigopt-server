/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import {Dropdown, DropdownItem} from "../../../component/dropdown";
import {InviteRoles} from "../../../user/roles";
import {getInviteRoleDisplayText} from "../../../user/helpers";

export const handleSuccess =
  (success, handler) =>
  (...args) => {
    const next = (...nextArgs) => success && success(...nextArgs);
    return handler ? handler(...args, next) : next(...args);
  };

export const catchError =
  (alertBroker, error, ...httpCodes) =>
  (err) => {
    alertBroker.errorHandlerThatExpectsStatus(...httpCodes)(err);
    return error && error(err);
  };

export class RolesDropdown extends React.Component {
  static propTypes = {
    disabled: PropTypes.bool.isRequired,
    onSelectRole: PropTypes.func.isRequired,
    selectedRole: PropTypes.oneOf(_.values(InviteRoles)).isRequired,
  };

  render() {
    return (
      <Dropdown
        buttonClassName="btn btn-sm btn-white-border dropdown-toggle"
        disabled={this.props.disabled}
        label={getInviteRoleDisplayText(this.props.selectedRole)}
      >
        {_.map(
          [InviteRoles.READ_ONLY, InviteRoles.USER, InviteRoles.ADMIN],
          (r) => (
            <DropdownItem active={r === this.props.selectedRole} key={r}>
              <a onClick={() => this.props.onSelectRole(r)} data-id={r}>
                {getInviteRoleDisplayText(r)}
              </a>
            </DropdownItem>
          ),
        )}
      </Dropdown>
    );
  }
}
