/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import PropTypes from "prop-types";
import React from "react";

const GenerateButton = (props) => (
  <button
    className={props.className}
    disabled={props.disabled}
    onClick={props.onClick}
    type="button"
  >
    {props.children}
  </button>
);

class GenerateSuggestionButton extends React.Component {
  static propTypes = {
    children: PropTypes.string.isRequired,
    className: PropTypes.string,
    createSuggestion: PropTypes.func,
    disabled: PropTypes.bool,
    error: PropTypes.func,
    onCreate: PropTypes.func,
  };

  render() {
    return (
      <GenerateButton
        className={this.props.className}
        disabled={this.props.disabled}
        onClick={() =>
          this.props.createSuggestion(this.props.onCreate, this.props.error)
        }
      >
        {this.props.children}
      </GenerateButton>
    );
  }
}

export default GenerateSuggestionButton;
