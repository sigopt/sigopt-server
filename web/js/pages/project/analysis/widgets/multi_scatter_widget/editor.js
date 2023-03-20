/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import {connect} from "react-redux";

import {ColorDimensionPicker} from "../../lib/color_dimension";
import {MultiDimensionSelect} from "../../components/dimension_select";
import {MultiScatterStateBuilder} from "./state";
import {WidgetTitleEditor} from "../../components/widget_title_editor";

// TODO: should centralize on a single form management system
// https://jaredpalmer.com/formik/ (?) other popular one seems hook only
const validateOptions = (xDimKeys, yDimKeys) => {
  const errors = [];

  if (xDimKeys.length === 0) {
    errors.push("At least one dimension must be selected for the X Axis");
  }
  if (yDimKeys.length === 0) {
    errors.push("At least one dimension must be selected for the Y Axis");
  }

  const isValid = errors.length === 0;

  return {isValid, errors};
};

const UnconnectedMultiScatterWidgetEditor = ({
  initialWidgetData,
  setWidgetData,
  setValid,
  dims,
}) => {
  const {state} = initialWidgetData;
  const [title, setTitle] = React.useState(initialWidgetData.title);
  const [xDimKeys, setxDimKeys] = React.useState(state.xDimKeys);
  const [yDimKeys, setyDimKeys] = React.useState(state.yDimKeys);
  const [colorState, setColorState] = React.useState(state.colorState);

  React.useEffect(() => {
    const {isValid, errors} = validateOptions(xDimKeys, yDimKeys);
    setValid(isValid, errors);

    if (isValid) {
      const newWidgetData = MultiScatterStateBuilder(
        title,
        xDimKeys,
        yDimKeys,
        colorState,
      );
      setWidgetData(newWidgetData);
    }
  }, [title, xDimKeys, yDimKeys, colorState]);

  return (
    <div className="flex-column">
      <WidgetTitleEditor title={title} setTitle={setTitle} />
      <div>
        <span>Y Axes:</span>
        <MultiDimensionSelect
          dims={dims}
          selectedDims={yDimKeys}
          setSelectedDims={setyDimKeys}
        />
      </div>
      <div>
        <span>X Axes:</span>
        <MultiDimensionSelect
          dims={dims}
          selectedDims={xDimKeys}
          setSelectedDims={setxDimKeys}
        />
      </div>
      <div>
        <span>Color:</span>
        <ColorDimensionPicker
          dims={dims}
          colorState={colorState}
          setColorState={setColorState}
        />
      </div>
    </div>
  );
};

const mapStateToProps = (state) => ({
  dims: state.dimensions.dimensions,
});

export const MultiScatterWidgetEditor = connect(mapStateToProps)(
  UnconnectedMultiScatterWidgetEditor,
);
