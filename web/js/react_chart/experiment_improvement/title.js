/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import {isDefinedAndNotNull} from "../../utils";

class ExperimentImprovementTitle extends React.Component {
  static propTypes = {
    metric: PropTypes.object.isRequired,
  };

  render() {
    const title = isDefinedAndNotNull(this.props.metric.name)
      ? `Experiment Improvement - ${this.props.metric.name}`
      : "Experiment Improvement";
    return <div className="title-label">{title}</div>;
  }
}

export default ExperimentImprovementTitle;
