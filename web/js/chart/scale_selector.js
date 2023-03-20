/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import schemas from "../react/schemas";
import {ParameterTransformations} from "../experiment/constants";

export const updateLayoutForScale = (axisToScale, layout) => {
  _.each(
    axisToScale,
    (scale, axis) => (layout[axis] = _.extend({}, layout[axis], {type: scale})),
  );
};

export class ScaleSelector extends React.Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    logScaleSelected: PropTypes.bool,
    onSelect: PropTypes.func,
    selectedAxis: PropTypes.string,
  };

  render() {
    // @TODO(SN-1008): can i pass in axis-type, aka parameter / metric / metadata
    // to more accurately decide when to show?
    const showScaleToggle = _.chain(this.props.experiment.parameters)
      .filter((p) => p.transformation === ParameterTransformations.LOG)
      .pluck("name")
      .contains(this.props.selectedAxis)
      .value();
    const id = Math.random().toString();
    return showScaleToggle ? (
      <div className="checkbox">
        <label htmlFor={id}>
          <input
            type="checkbox"
            id={id}
            checked={this.props.logScaleSelected}
            onChange={(e) => this.props.onSelect(e.target.checked)}
          />
          {""}
          Log Scale
        </label>
      </div>
    ) : null;
  }
}
