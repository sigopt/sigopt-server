/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

class Header extends React.Component {
  static propTypes = {
    active: PropTypes.bool,
    children: PropTypes.node,
    className: PropTypes.string,
    colSpan: PropTypes.number,
    onClick: PropTypes.func,
    sortAscending: PropTypes.bool,
    sortFunc: PropTypes.func,
    sortKey: PropTypes.string,
    sortable: PropTypes.bool,
    title: PropTypes.string,
  };

  static defaultProps = {
    active: false,
    sortAscending: false,
    sortable: false,
  };

  onClick = (e) => {
    if (this.props.sortable && this.props.onClick) {
      e.preventDefault();
      e.stopPropagation();
      this.props.onClick(
        this.props.sortKey,
        !this.props.sortAscending,
        this.props.sortFunc,
      );
    }
  };

  render() {
    const className = classNames(
      {
        active: this.props.active,
        ascending: this.props.sortAscending,
        descending: !this.props.sortAscending,
      },
      this.props.className,
    );
    return (
      <th
        className={className}
        colSpan={this.props.colSpan}
        onClick={this.onClick}
        title={this.props.title}
      >
        {this.props.sortable ? (
          <a>{this.props.children}</a>
        ) : (
          this.props.children
        )}
      </th>
    );
  }
}

export default Header;
