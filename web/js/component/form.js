/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import {withPreventDefault} from "../utils";

class Form extends React.Component {
  static propTypes = {
    acceptCharset: PropTypes.string,
    action: PropTypes.string,
    children: PropTypes.node,
    className: PropTypes.string,
    csrfToken: PropTypes.string,
    encType: PropTypes.string,
    forwardedRef: PropTypes.object,
    method: PropTypes.string,
    onSubmit: PropTypes.func,
    style: PropTypes.object,
  };

  render() {
    const method = this.props.method || "post";
    return (
      <form
        acceptCharset={this.props.acceptCharset}
        action={this.props.action}
        className={classNames("form", "tracked", this.props.className)}
        encType={this.props.encType}
        method={method}
        onSubmit={
          this.props.onSubmit && withPreventDefault(this.props.onSubmit)
        }
        ref={this.props.forwardedRef}
        style={this.props.style}
      >
        {this.props.children}
        {method === "post" && (
          <input
            type="hidden"
            name="csrf_token"
            value={this.props.csrfToken || ""}
          />
        )}
      </form>
    );
  }
}

export default React.forwardRef((props, ref) => (
  <Form {...props} forwardedRef={ref} />
));
