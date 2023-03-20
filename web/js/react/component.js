/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import schemas from "./schemas";

export default class Component extends React.Component {
  static get contextTypes() {
    return {
      loginState: schemas.LoginState,
      pageRenderTime: PropTypes.number,
      services: schemas.Services,
    };
  }

  get services() {
    return this.context.services;
  }
}
