/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Spinner from "./spinner";

class Loading extends React.Component {
  static propTypes = {
    children: PropTypes.node,
    empty: PropTypes.bool,
    emptyMessage: PropTypes.object,
    loading: PropTypes.bool,
    size: PropTypes.number,
  };

  render() {
    if (this.props.loading) {
      return <Spinner size={this.props.size} position="absolute" />;
    } else if (this.props.empty) {
      return this.props.emptyMessage ? (
        this.props.emptyMessage
      ) : (
        <p>{"You have no data at this time"}</p>
      );
    } else {
      return <span>{this.props.children}</span>;
    }
  }
}

export default Loading;
