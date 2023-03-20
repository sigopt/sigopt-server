/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../render/bootstrap";

import $ from "jquery";
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import ReactDOM from "react-dom";
import classNames from "classnames";

import Component from "../../react/component";
import {MODAL_ROOT_ID} from "./constant";

/**
 * An unstyled Modal, just the boilerplate for showing/hiding/dismissing
 */
export default class RawModal extends Component {
  static propTypes = {
    alertHandler: PropTypes.func,
    children: PropTypes.node.isRequired,
    className: PropTypes.string,
    id: PropTypes.string,
    noClose: PropTypes.bool,
    onClose: PropTypes.func,
  };

  static defaultProps = {
    onClose: _.noop,
  };

  state = {
    hasBeenMadeVisible: false,
    modalId: `raw-modal-${Math.random()}`,
    visible: false,
  };

  componentDidUpdate(prevProps, prevState) {
    if (
      prevProps.alertHandler !== this.props.alertHandler &&
      this.services.alertBroker &&
      this.services.alertBroker.hasRegisteredHandler(prevProps.alertHandler)
    ) {
      this.services.alertBroker.releaseHandler(prevProps.alertHandler);
      this.services.alertBroker.registerHandler(this.props.alertHandler);
    }

    const shouldHide = prevState.visible && !this.state.visible;
    const shouldShow = !prevState.visible && this.state.visible;

    const $modal = this.$modal();
    if (shouldHide) {
      $modal.modal("hide");
      this.props.onClose();
    }
    if (shouldShow) {
      $modal.modal("show");
      this.registerAlertHandler();
      $modal.on("hide.bs.modal", this.releaseAlertHandler);
      $modal.on("hide.bs.modal", () => this.hide());
    }
  }

  componentWillUnmount() {
    this.$modal().off("hidden.bs.modal", this.props.onClose);
  }

  modalElement() {
    return document.getElementById(MODAL_ROOT_ID);
  }

  $modal() {
    return $(document.getElementById(this.state.modalId)).find(".modal");
  }

  registerAlertHandler = () => {
    if (this.services.alertBroker) {
      this.services.alertBroker.registerHandler(this.props.alertHandler);
    }
  };

  show = (cb) => {
    this.setState({visible: true, hasBeenMadeVisible: true}, cb);
  };

  releaseAlertHandler = () => {
    if (this.services.alertBroker) {
      this.services.alertBroker.releaseHandler(this.props.alertHandler);
    }
  };

  hide = (callback) => {
    this.setState({visible: false}, callback);
  };

  render() {
    if (this.state.hasBeenMadeVisible) {
      return ReactDOM.createPortal(
        <div id={this.state.modalId}>
          <div
            aria-hidden="true"
            className={classNames("modal", "fade", this.props.className)}
            data-backdrop={this.props.noClose ? "static" : true}
            data-keyboard={this.props.noClose ? false : null}
            id={this.props.id}
            onMouseDown={this.props.noClose ? null : () => this.hide()}
            role="dialog"
            tabIndex="-1"
          >
            {this.props.children}
          </div>
        </div>,
        this.modalElement(),
      );
    } else {
      return null;
    }
  }
}
