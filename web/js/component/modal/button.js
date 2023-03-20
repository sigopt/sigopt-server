/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

const buttonValidator = (props) =>
  Boolean(props.button) ^ Boolean(props.label)
    ? null
    : new Error("Exactly one of `button` or `label` must be specified");

export default class TriggerModalButton extends React.Component {
  static propTypes = {
    button: buttonValidator,
    children: PropTypes.element.isRequired,
    disabled: PropTypes.bool,
    label: buttonValidator,
    onClick: PropTypes.func,
  };

  static defaultProps = {
    disabled: false,
  };

  render() {
    const modal = React.cloneElement(this.props.children, {
      ref: (c) => {
        this._modal = c;
        // Preserve original ref, if any
        // https://github.com/facebook/react/issues/8873
        const originalRef = this.props.children.ref;
        if (typeof originalRef === "function") {
          originalRef(c);
        }
      },
    });

    const ourOnClick = (...args) => {
      if (!this.props.disabled) {
        this._modal.show();
        if (this.props.onClick) {
          this.props.onClick(...args);
        }
      }
    };

    const attachedButton = this.props.button || <a>{this.props.label}</a>;
    const buttonProps = _.omit(
      this.props,
      "button",
      "children",
      "label",
      "onClick",
    );

    return (
      <>
        {modal}
        {React.cloneElement(
          attachedButton,
          _.extend({onClick: ourOnClick}, buttonProps),
        )}
      </>
    );
  }
}
