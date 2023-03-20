/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import CircleGlyph from "../component/glyph/circle";
import Component from "../react/component";

class TabLink extends Component {
  static propTypes = {
    children: PropTypes.node.isRequired,
    glyph: PropTypes.node,
    href: PropTypes.string.isRequired,
    path: PropTypes.string,
  };

  static defaultProps = {
    glyph: <CircleGlyph />,
  };

  render() {
    const active = this.props.path === this.props.href;
    return (
      <a
        href={this.props.href}
        className={classNames(active && "active", "glyph-label")}
        role="presentation"
      >
        {this.props.glyph}
        <span className="link-label">{this.props.children}</span>
      </a>
    );
  }
}

export default TabLink;
