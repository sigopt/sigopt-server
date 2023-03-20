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

export default class UndeleteButton extends Component {
  static propTypes = {
    handleClick: PropTypes.func.isRequired,
  };

  render() {
    return (
      <ActionButton onClick={this.props.handleClick} success={refreshPage}>
        Unarchive
      </ActionButton>
    );
  }
}
