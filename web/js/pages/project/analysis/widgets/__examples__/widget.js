/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import {connect} from "react-redux";

import {DimensionSelect} from "../../components/dimension_select";
import {getDimension} from "../../lib/dimensions";
import {
  setHoverInfo,
  setSelectedIndexes,
} from "../../../state/dimensions_slice";

const DimInfo = ({dims, dimKey}) => {
  const dim = getDimension(dims, dimKey);
  return (
    <div className="flex-column">
      <div>Dimension Name: {dim.displayName}</div>
      <div>Dimension # times defined: {dim.count} </div>
      <div>Dimension Value Type: {dim.valueType} </div>
      {dim.categoricalValues ? (
        <div>Categorical Values: [{dim.categoricalValues.join(" ")}] </div>
      ) : null}
    </div>
  );
};

class UnconnectedExampleWidget extends React.Component {
  onTextBoxChange = (event) => {
    this.props.updateWidget((widget) => {
      widget.state.exampleText = event.target.value;
    });
  };

  updateDimension = (selectedDim) => {
    this.props.updateWidget((widget) => {
      widget.state.selectedDimKey = selectedDim;
    });
  };

  render() {
    const widgetState = this.props.widget.state;
    return (
      <div>
        Hi currently run: {this.props.hoverId} is being hovered.
        <br />
        In total there are: {_.values(this.props.dims).length} dimensions, pick
        one to get some info.
        <DimensionSelect
          dims={this.props.dims}
          selectedDim={widgetState.selectedDimKey}
          setSelectedDim={this.updateDimension}
        />
        {widgetState.selectedDimKey ? (
          <DimInfo dims={this.props.dims} dimKey={widgetState.selectedDimKey} />
        ) : null}
        <br />
        {""}Want see what state is avaliable to use?
        <a href="https://chrome.google.com/webstore/detail/redux-devtools/lmhkpmbekcpmknklioeibfkpmmfibljd?hl=en">
          {" "}
          Use Redux Dev Tools
        </a>
        <textarea
          onChange={this.onTextBoxChange}
          value={widgetState.exampleText}
        />
      </div>
    );
  }
}

// These all will become props. Read only, Do not try to mutate any of these.
// If you need to make changes do so through mapDispatchToProps
// or you can use updateWidget to update the current widget
// which is injected automatically via props by the dashboard.
const mapStateToProps = (state) => ({
  dims: state.dimensions.dimensions,
  selectedBySource: state.dimensions.selectedBySource,
  hoverId: state.dimensions.hoverInfo.hoverId,
});

// If you want to change stuff it needs to be through an action
const mapDispatchToProps = {setSelectedIndexes, setHoverInfo};

export const ExampleWidget = connect(
  mapStateToProps,
  mapDispatchToProps,
)(UnconnectedExampleWidget);
