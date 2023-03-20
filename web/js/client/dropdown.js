/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import schemas from "../react/schemas";
import {Dropdown, DropdownItem} from "../component/dropdown";

export default class ClientsDropdown extends React.Component {
  static propTypes = {
    allowBlank: PropTypes.bool.isRequired,
    blankLabel: PropTypes.string,
    buttonClassName: PropTypes.string,
    clients: PropTypes.arrayOf(schemas.Client.isRequired),
    disabled: PropTypes.bool,
    onClientSelect: PropTypes.func.isRequired,
    selectedClient: schemas.Client,
  };

  static defaultProps = {
    buttonClassName: "btn clients-dropdown-btn dropdown-toggle",
    disabled: false,
  };

  render() {
    return (
      <Dropdown
        buttonClassName={this.props.buttonClassName}
        disabled={this.props.disabled || _.size(this.props.clients) <= 1}
        label={
          this.props.selectedClient
            ? this.props.selectedClient.name
            : this.props.blankLabel
        }
      >
        {this.props.allowBlank && (
          <DropdownItem active={!this.props.selectedClient} key="blank-label">
            <a onClick={() => this.props.onClientSelect(null)}>
              {this.props.blankLabel}
            </a>
          </DropdownItem>
        )}
        {_.map(this.props.clients, (client) => (
          <DropdownItem
            active={
              Boolean(this.props.selectedClient) &&
              client.id === this.props.selectedClient.id
            }
            key={client.id}
          >
            <a
              onClick={() => this.props.onClientSelect(client)}
              data-id={client.id}
            >
              {client.name}
            </a>
          </DropdownItem>
        ))}
      </Dropdown>
    );
  }
}
