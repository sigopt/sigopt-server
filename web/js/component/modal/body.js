/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import Alert from "../../alert/alert";
import AlertPanel from "../../alert/panel";

/**
 * The section of the Modal containing free-form content, such as
 * error messages or form fields.
 */
const ModalBody = (props) => {
  if (props.submitted && props.submittedContent) {
    return <div className="modal-body">{props.submittedContent}</div>;
  }
  if (props.children || props.error) {
    return (
      <div className="modal-body">
        {props.error && (
          <AlertPanel error={props.error} onDismiss={props.onAlertDismiss} />
        )}
        {props.children}
      </div>
    );
  }
  return null;
};

ModalBody.propTypes = {
  children: PropTypes.node,
  error: PropTypes.instanceOf(Alert),
  onAlertDismiss: PropTypes.func,
  submitted: PropTypes.bool,
  submittedContent: PropTypes.node,
};

ModalBody.defaultProps = {
  submitted: false,
};

export default ModalBody;
