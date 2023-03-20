/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import {connect} from "react-redux";

import {DimensionSelect} from "../../components/dimension_select";
import {ExampleStateBuilder} from "./state";

/**
 * @typedef {import('./state').ExampleWidgetState} ExampleWidgetState
 */

const validateWidgetState = (editorDimKey) => {
  const errors = [];
  if (!editorDimKey) {
    errors.push("Must selected a dimension from the editor");
  }

  const isValid = errors.length === 0;

  return {isValid, errors};
};

const UnconnectedExampleWidgetEditor = ({
  initialWidgetData,
  setWidgetData,
  setValid,
  dims,
}) => {
  const {state} = initialWidgetData;
  const [editorDimKey, setEditorDimKey] = React.useState(state.editorDimKey);

  React.useEffect(() => {
    const {isValid, errors} = validateWidgetState(editorDimKey);
    setValid(isValid, errors);

    if (isValid) {
      const newWidgetData = ExampleStateBuilder(
        initialWidgetData.title,
        initialWidgetData.exampleText,
        initialWidgetData.state.selectedDimKey,
        editorDimKey,
      );
      setWidgetData(newWidgetData);
    }
  }, [editorDimKey]);

  return (
    <div>
      <div>Select a dimension from editor.</div>
      <DimensionSelect
        dims={dims}
        selectedDim={editorDimKey}
        setSelectedDim={setEditorDimKey}
      />
    </div>
  );
};

const mapStateToProps = (state) => ({
  dims: state.dimensions.dimensions,
});

export const ExampleWidgetEditor = connect(mapStateToProps)(
  UnconnectedExampleWidgetEditor,
);
