/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import ActionButton from "../action_button";
import Component from "../../react/component";
import refreshPage from "../../net/refresh";

export default class ArchiveButton extends Component {
  static propTypes = {
    handleClick: PropTypes.func.isRequired,
    label: PropTypes.string.isRequired,
  };

  render() {
    return (
      <ActionButton
        className="btn btn-danger"
        onClick={this.props.handleClick}
        success={refreshPage}
      >
        {this.props.label}
      </ActionButton>
    );
  }
}
