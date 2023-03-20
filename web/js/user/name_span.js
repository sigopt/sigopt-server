/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import Spinner from "../component/spinner";

class AsynchronousUserName extends React.Component {
  state = {
    user: null,
    hasUser: false,
  };

  componentDidMount() {
    this.componentDidUpdate();
  }

  componentDidUpdate() {
    if (!this.state.hasUser && this.props.dataSource) {
      this.props.dataSource.getData((user) => {
        this.setState({user: user, hasUser: true});
      });
    }
  }

  render() {
    const text = (this.state.user && this.state.user.name) || "Unknown";
    return this.state.hasUser ? (
      <span title={text}>{text}</span>
    ) : (
      <Spinner className="created-by-spinner" size={7} position="relative" />
    );
  }
}

export default AsynchronousUserName;
