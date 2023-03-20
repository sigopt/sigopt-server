/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./spinner.less";

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import Component from "../react/component";

class RealSpinnerHolder extends Component {
  render() {
    return (
      <div
        className={classNames("spinner", "loading", this.props.className)}
        id={this.props.id ? this.props.id : null}
        style={{height: this.props.boxSize}}
      />
    );
  }
}

class ReactSpinner extends React.Component {
  static propTypes = {
    className: PropTypes.string,
    id: PropTypes.string,
    loading: PropTypes.bool,
    position: PropTypes.string,
    size: PropTypes.number,
  };

  static defaultProps = {
    loading: true,
    position: "relative",
  };

  // Default values are taken from http://fgnass.github.io/spin.js/spin.js
  width = () => (this.props.size ? (this.props.size * 10) / 50 : 5);

  length = () => (this.props.size ? (this.props.size * 20) / 50 : 7);

  radius = () => (this.props.size ? (this.props.size * 30) / 50 : 10);

  render() {
    if (this.props.loading) {
      const boxSize = 2 * (this.radius() + this.length() + this.width());

      return (
        <RealSpinnerHolder
          boxSize={boxSize}
          className={this.props.className}
          id={this.props.id}
          position={this.props.position}
          length={this.length()}
          radius={this.radius()}
          width={this.width()}
        />
      );
    } else {
      return null;
    }
  }
}

export default ReactSpinner;
