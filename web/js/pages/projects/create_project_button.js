/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import ProjectModal from "./project_modal";
import TriggerModalButton from "../../component/modal/button";

class CreateProjectButton extends React.Component {
  static propTypes = {
    className: PropTypes.string,
    onClick: PropTypes.func,
  };

  static defaultProps = {
    className: "btn btn-secondary",
  };

  render() {
    return (
      <TriggerModalButton
        className={this.props.className}
        label="Create Project"
      >
        <ProjectModal {...this.props} />
      </TriggerModalButton>
    );
  }
}

export default CreateProjectButton;
