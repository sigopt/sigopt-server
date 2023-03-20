/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import Tooltip from "./tooltip";

class TooltipInput extends React.Component {
  static propTypes = {
    className: PropTypes.string,
    label: PropTypes.string.isRequired,
    placeholder: PropTypes.string,
    setter: PropTypes.func.isRequired,
    tooltip: PropTypes.string.isRequired,
    value: PropTypes.string,
  };

  render() {
    let label = null;
    if (this.props.label) {
      label = (
        <Tooltip tooltip={this.props.tooltip}>
          <label className="control-label">{this.props.label}</label>
        </Tooltip>
      );
    }
    return (
      <div className={classNames("form-group", this.props.className)}>
        {label}
        <input
          required={true}
          type="text"
          className="form-control"
          placeholder={this.props.placeholder || this.props.label}
          onChange={this.props.setter}
          value={this.props.value || ""}
        />
      </div>
    );
  }
}

export default TooltipInput;
