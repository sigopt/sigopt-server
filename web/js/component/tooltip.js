/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./tooltip.less";

import PropTypes from "prop-types";
import React from "react";

import CircleQuestionGlyph from "./glyph/circle-question";
import CustomTooltip from "./custom_tooltip";

class Tooltip extends React.Component {
  static propTypes = {
    children: PropTypes.node.isRequired,
    html: PropTypes.bool,
    iconFirst: PropTypes.bool,
    tooltip: PropTypes.node.isRequired,
  };

  static defaultProps = {
    iconFirst: false,
  };

  render() {
    return (
      <CustomTooltip html={this.props.html} tooltip={this.props.tooltip}>
        {!this.props.iconFirst && this.props.children}
        <span className="tooltip-trigger">
          <CircleQuestionGlyph />
        </span>
        {this.props.iconFirst ? this.props.children : null}
      </CustomTooltip>
    );
  }
}

export default Tooltip;
