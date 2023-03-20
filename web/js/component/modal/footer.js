/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Spinner from "../spinner";
import {FooterTypes} from "./constant";

/**
 * The bottom row of the modal, where action butons are located.
 * Accepts an instance of `FooterTypes` to choose which buttons to render
 */
const ModalFooter = (props) => {
  if (props.footer === FooterTypes.None) {
    return null;
  } else {
    if (props.submitting) {
      return (
        <div className="modal-footer">
          <Spinner position="absolute" />
        </div>
      );
    }

    const submitButton = _.contains(
      [FooterTypes.Submit, FooterTypes.SubmitAndCancel],
      props.footer,
    ) && (
      <input
        disabled={props.submitting || props.submitted || !props.isValid}
        className={props.submitButtonClass}
        type="submit"
        value={props.submitButtonLabel}
      />
    );

    const cancelButton = _.contains(
      [FooterTypes.Cancel, FooterTypes.SubmitAndCancel],
      props.footer,
    ) && (
      <a
        disabled={props.submitting || props.cancelDisabled}
        tabIndex={submitButton ? "-1" : undefined}
        className={props.cancelButtonClass}
        data-dismiss={props.cancelDisabled ? null : "modal"}
      >
        {props.cancelButtonLabel}
      </a>
    );

    return (
      <div className="modal-footer">
        {cancelButton}
        {submitButton}
      </div>
    );
  }
};

ModalFooter.propTypes = {
  cancelButtonClass: PropTypes.string,
  cancelButtonLabel: PropTypes.string,
  cancelDisabled: PropTypes.bool,
  footer: PropTypes.oneOf(_.values(FooterTypes)),
  isValid: PropTypes.bool,
  submitButtonClass: PropTypes.string,
  submitButtonLabel: PropTypes.string,
  submitted: PropTypes.bool,
  submitting: PropTypes.bool,
};

ModalFooter.defaultProps = {
  cancelButtonClass: "btn btn-white-border",
  cancelButtonLabel: "Cancel",
  cancelDisabled: false,
  footer: FooterTypes.None,
  isValid: true,
  submitButtonClass: "btn btn-primary",
  submitButtonLabel: "Submit",
  submitted: false,
  submitting: false,
};

export default ModalFooter;
