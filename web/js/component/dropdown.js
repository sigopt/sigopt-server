/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../render/bootstrap";

import $ from "jquery";
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

class BaseDropdownItem extends React.Component {
  static propTypes = {
    active: PropTypes.bool,
    children: PropTypes.node.isRequired,
    className: PropTypes.string,
  };

  render() {
    return (
      <li
        className={classNames(this.props.className, {
          active: this.props.active,
        })}
        role="presentation"
      >
        {this.props.children}
      </li>
    );
  }
}

export const DropdownItem = (props) => <BaseDropdownItem {...props} />;

export const DropdownHeader = (props) => (
  <BaseDropdownItem
    {...props}
    className={classNames(props.className, "dropdown-header")}
  />
);

export class Dropdown extends React.Component {
  static propTypes = {
    button: PropTypes.node,
    buttonClassName: PropTypes.string,
    caret: PropTypes.bool,
    children: PropTypes.node,
    direction: PropTypes.oneOf(["down", "up"]),
    disabled: PropTypes.bool,
    label: PropTypes.node,
  };

  static defaultProps = {
    buttonClassName: "btn btn-default",
    caret: true,
    direction: "down",
    disabled: false,
  };

  constructor(...args) {
    super(...args);
    this._node = React.createRef();
  }

  componentDidMount() {
    this.$dropdown = $(this._node.current);
    this.$dropdown.find(".dropdown-toggle").dropdown();
  }

  open() {
    if (!this.$dropdown[0].classList.contains("open")) {
      this.$dropdown.dropdown("toggle");
    }
  }

  close() {
    if (this.$dropdown[0].classList.contains("open")) {
      this.$dropdown.dropdown("toggle");
    }
  }

  render() {
    const button = this.props.button || (
      <button
        type="button"
        style={{verticalAlign: "middle"}}
        className={this.props.buttonClassName}
        disabled={this.props.disabled}
        title={this.props.label}
      >
        {/*
        We inline the style here because it is important to get this right -
        in Firefox the `float: right` element needs to come first, otherwise the
        alignment is all broken
        */}
        {this.props.caret && (
          <div style={{float: "right", marginLeft: "4px"}}>
            <span className="caret" />
          </div>
        )}
        {this.props.label && (
          <span className="dropdown-btn-label">{this.props.label}</span>
        )}
        <span className="sr-only">Toggle Dropdown</span>
      </button>
    );
    const dropdownProps = _.omit(
      this.props,
      "button",
      "buttonClassName",
      "caret",
      "children",
      "direction",
      "disabled",
      "label",
    );
    const className = this.props.direction === "up" ? "dropup" : "dropdown";
    return (
      <div className={className} {...dropdownProps} ref={this._node}>
        {React.cloneElement(button, {
          className: classNames(button.props.className, "dropdown-toggle"),
          "data-toggle": "dropdown",
          disabled: this.props.disabled,
          type: "button",
        })}
        <ul className="dropdown-menu" role="menu">
          {this.props.children}
        </ul>
      </div>
    );
  }
}
