/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Form from "../form";
import makeSubmittableComponent from "../make-submittable";
import {MakeModal} from "./base";

const FormModal = MakeModal((props) => (
  <Form {...props}>{props.children}</Form>
));

/**
 * A Modal that includes a Form. Uses Submittable to safely handle submissions
 */
const ModalForm = makeSubmittableComponent(
  class extends React.Component {
    static displayName = "ModalForm";

    static propTypes = {
      action: PropTypes.string,
      children: PropTypes.node.isRequired,
      closeDelay: PropTypes.number,
      csrfToken: PropTypes.string,
      error: PropTypes.func,
      hideOnSuccess: PropTypes.bool,
      onSubmit: PropTypes.func,
      resetSubmissionState: PropTypes.func.isRequired,
      submit: PropTypes.func.isRequired,
      submitted: PropTypes.bool.isRequired,
      submitting: PropTypes.bool.isRequired,
      success: PropTypes.func,
    };

    static defaultProps = {
      closeDelay: 1500,
      hideOnSuccess: true,
    };

    submit = () =>
      this.props.submit(this.props.onSubmit, this.success, this.props.error);

    success = (...args) => {
      if (this.props.hideOnSuccess) {
        _.delay(
          () =>
            this.hide(() => this.props.success && this.props.success(...args)),
          this.props.closeDelay,
        );
      } else if (this.props.success) {
        this.props.success(...args);
      }
    };

    clearAlerts = () => this._modal.clearAlerts();

    show = (cb) => {
      this.props.resetSubmissionState();
      this._modal.show(cb);
    };

    hide = (cb) => {
      if (this._modal) {
        this._modal.hide(cb);
      }
    };

    render() {
      return (
        <FormModal
          {..._.omit(this.props, "onSubmit")}
          action={this.props.action}
          csrfToken={this.props.csrfToken}
          onSubmit={this.props.onSubmit && this.submit}
          ref={(c) => {
            this._modal = c;
          }}
        >
          {this.props.children}
        </FormModal>
      );
    }
  },
);

export default ModalForm;
