/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import CheckGlyph from "./glyph/check";
import Spinner from "./spinner";
import makeSubmittableComponent from "./make-submittable";
import {withPreventDefaultAndStopPropagation} from "../utils";

const ActionButton = makeSubmittableComponent(
  class ActionButton extends React.Component {
    static propTypes = {
      children: PropTypes.node.isRequired,
      className: PropTypes.string,
      disabled: PropTypes.bool,
      error: PropTypes.func,
      onClick: PropTypes.func.isRequired,
      size: PropTypes.string,
      submit: PropTypes.func.isRequired,
      submitted: PropTypes.bool.isRequired,
      submitting: PropTypes.bool.isRequired,
      success: PropTypes.func,
    };

    static defaultProps = {
      error: _.noop,
      success: _.noop,
    };

    onClick = withPreventDefaultAndStopPropagation(() =>
      this.props.submit(
        (s, e) => this.props.onClick().then(s, e),
        this.props.success,
        this.props.error,
      ),
    );

    render() {
      const size = this.props.size || "md";
      if (this.props.submitted) {
        return (
          <a className={`btn btn-success btn-${size}`} disabled={true}>
            <CheckGlyph />
          </a>
        );
      } else if (this.props.submitting) {
        return (
          <span style={{position: "relative"}}>
            <Spinner />
          </span>
        );
      } else {
        return (
          <button
            className={classNames(
              this.props.className || "btn btn-primary",
              `btn-${size}`,
            )}
            disabled={this.props.disabled || false}
            onClick={this.onClick}
            type="button"
          >
            {this.props.children}
          </button>
        );
      }
    }
  },
);

export default ActionButton;
