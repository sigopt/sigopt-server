/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./style.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import ArrowsRotateGlyph from "../glyph/arrows-rotate";

export default class RefreshButton extends React.Component {
  static propTypes = {
    onRefreshFinished: PropTypes.func,
    refresh: PropTypes.func.isRequired,
  };

  static defaultProps = {
    onRefreshFinished: _.noop,
  };

  state = {refreshP: null, refreshData: {}};

  componentDidUpdate(prevProps, prevState) {
    if (this.state.refreshP && this.state.refreshP !== prevState.refreshP) {
      this.state.refreshP.then((data) =>
        this.setState({refreshP: null, refreshData: {data}}),
      );
    }
    if (this.state.refreshData !== prevState.refreshData) {
      this.props.onRefreshFinished(this.state.refreshData.data);
    }
  }

  refresh = () => {
    const refreshP = this.props.refresh();
    this.setState({refreshP});
  };

  render() {
    const refreshing = Boolean(this.state.refreshP);
    return (
      <a
        className={classNames("refresh-btn", "btn", "btn-primary", {
          refreshing,
        })}
        onClick={this.refresh}
        disabled={refreshing}
      >
        <ArrowsRotateGlyph />
      </a>
    );
  }
}
