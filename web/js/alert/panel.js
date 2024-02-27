/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Alert from "./alert";

class AlertPanel extends React.Component {
  static propTypes = {
    error: PropTypes.instanceOf(Alert).isRequired,
    onDismiss: PropTypes.func,
  };

  state = {
    dismissed: false,
  };

  dismiss = () => {
    this.setState(
      {dismissed: true},
      this.props.onDismiss || this.props.error.onDismiss,
    );
  };

  render() {
    const type = this.props.error.type || "danger";
    const useHtml = Boolean(this.props.error.dangerousHtml());
    return (
      !this.state.dismissed && (
        <div className={`alert alert-${type}`}>
          <button
            aria-label="Close"
            className="close"
            onClick={this.dismiss}
            type="button"
          >
            <span aria-hidden="true">&times;</span>
          </button>
          {useHtml ? (
            <p
              className="alert-message"
              dangerouslySetInnerHTML={this.props.error.dangerousHtml()}
            />
          ) : (
            <p className="alert-message">{this.props.error.message}</p>
          )}
        </div>
      )
    );
  }
}

export default AlertPanel;
