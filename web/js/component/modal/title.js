/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

/**
 * The top row of a Modal, where the title and dismiss buttons are located
 */
const ModalTitle = (props) => {
  if (props.title) {
    return (
      <div className="modal-header">
        {props.showClose && (
          <button
            type="button"
            tabIndex="-1"
            className="close"
            data-dismiss="modal"
            aria-label="Close"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        )}
        <h4 className="modal-title">{props.title}</h4>
      </div>
    );
  } else {
    return null;
  }
};

ModalTitle.propTypes = {
  showClose: PropTypes.bool.isRequired,
  title: PropTypes.node,
};

export default ModalTitle;
