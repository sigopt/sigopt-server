/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import Component from "../../react/component";
import ModalInterior from "./interior";
import RawModal from "./raw";

/**
 * A React higher-order component for constructing a styled Modal class.
 * The metaclass is necessary so we can wrap the interior if necessary,
 * which is necessary for ModalForm.
 */
export const MakeModal = (Adapter) =>
  class extends Component {
    static get propTypes() {
      return {
        children: PropTypes.node.isRequired,
        className: PropTypes.string,
        id: PropTypes.string,
        noClose: PropTypes.bool,
        onClose: PropTypes.func,
        validator: PropTypes.func,
      };
    }

    constructor(props) {
      super(props);
      this.state = {
        error: null,
      };
      this.alertHandler = _.bind(this.alertHandler, this);
    }

    isValid = () => {
      if (this.props.validator) {
        return Boolean(this.props.validator(this));
      } else {
        return true;
      }
    };

    alertHandler = (lert) => {
      this.setState({error: lert});
    };

    clearAlerts = () => {
      this.setState({error: null});
    };

    show = (cb) => this._modal.show(cb);

    hide = (callback) => {
      this._modal.hide(callback);
    };

    render() {
      return (
        <RawModal
          alertHandler={this.alertHandler}
          className={classNames("modal", "fade", this.props.className)}
          id={this.props.id}
          noClose={this.props.noClose}
          onClose={this.props.onClose}
          ref={(c) => {
            this._modal = c;
          }}
        >
          <Adapter {...this.props}>
            <ModalInterior
              {...this.props}
              error={this.state.error}
              isValid={this.isValid()}
              onAlertDismiss={this.clearAlerts}
              showClose={!this.props.noClose}
            >
              {this.props.children}
            </ModalInterior>
          </Adapter>
        </RawModal>
      );
    }
  };

/**
 * A standard Modal
 */
export default MakeModal((props) => <span>{props.children}</span>);
