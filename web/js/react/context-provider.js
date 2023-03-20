/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import schemas from "../react/schemas";

export default class ContextProvider extends React.Component {
  static get childContextTypes() {
    return {
      loginState: schemas.LoginState,
      pageRenderTime: PropTypes.number,
      services: schemas.Services,
    };
  }

  getChildContext() {
    return {
      loginState: this.props.loginState,
      pageRenderTime: this.props.pageRenderTime,
      services: this.props.services,
    };
  }

  render() {
    return this.props.children;
  }
}
