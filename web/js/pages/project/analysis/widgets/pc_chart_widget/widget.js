/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import Plotly from "plotly.js-strict-dist";
import React from "react";
import ReactDOM from "react-dom";
import {connect} from "react-redux";

import {MultiDimensionSelect} from "../../components/dimension_select";
import {PCChartStateBuilder} from "./state";
import {
  createColorDimensionGradient,
  createColorDimensionWithSelect,
} from "../../lib/color_dimension";
import {getPossibleDimensions} from "../../lib/dimensions";
import {parallelCoordinatesTemplates} from "../../../../../react_chart/parallel_coordinates/template";

const makePCChart = (dims) => {
  const chart = _.extend({}, parallelCoordinatesTemplates.base_template);

  // Plotly handles categoricals weirdly for PC charts.
  const plotlyDims = _.map(dims, (dim) => {
    const clonedDim = _.clone(dim);
    if (clonedDim.valueType === "CATEGORICAL") {
      clonedDim.values = clonedDim.plotlyValues;
    }
    return clonedDim;
  });

  chart.data[0].dimensions = plotlyDims;
  chart.options.responsive = true;

  return chart;
};

class ParallelCoordinatesWidget extends React.Component {
  constructor(props) {
    super(props);

    const graphID = Math.random().toString();

    this.state = {
      graphID,
    };
  }

  componentDidMount() {
    const node = ReactDOM.findDOMNode(this);
    node.addEventListener("resize", () => {
      Plotly.Plots.resize(this.state.graphID);
    });
    setTimeout(() => this.drawChart(), 30);
  }

  updateDimensions = (selectedDims) => {
    this.props.updateWidget((widget) => {
      widget.state.selectedDims = selectedDims;
    });

    _.defer(() => this.drawChart());
  };

  componentDidUpdate(prevProps) {
    if (!this.props.widget.state) {
      return;
    }

    if (this.props.dims !== prevProps.dims) {
      _.defer(() => this.drawChart());
    }

    if (this.props.selectedIndexes !== prevProps.selectedIndexes) {
      _.defer(() => this.drawChart());
    }
  }

  drawChart() {
    const {dims: dimsToPlot} = getPossibleDimensions(
      this.props.dims,
      this.props.widget.state.selectedDims,
    );
    const chartData = makePCChart(dimsToPlot);
    const {data, layout, options} = chartData;

    let graphColors = {color: "#6699ff"};
    const shouldHighlightPoints = this.props.selectedIndexes.length > 0;
    const colorState = this.props.widget.state.colorState;
    if (shouldHighlightPoints) {
      graphColors = createColorDimensionWithSelect(
        dimsToPlot[0].values.length,
        this.props.selectedIndexes,
      );
    } else if (colorState) {
      graphColors = createColorDimensionGradient(this.props.dims, colorState);
    }

    data[0].line.color = graphColors.color;
    data[0].line.colorscale = graphColors.colorscale;

    if (this.state.drawn) {
      Plotly.react(this.state.graphID, data, layout, options);
      this.setState({drawn: true});
    } else {
      Plotly.newPlot(this.state.graphID, data, layout, options);
    }
  }

  render() {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          width: "100%",
        }}
      >
        <div id={this.state.graphID} style={{width: "100%", flexGrow: 1}} />
        <div style={{flexShrink: 1}}>
          <MultiDimensionSelect
            dims={this.props.dims}
            selectedDims={this.props.widget.state.selectedDims}
            setSelectedDims={this.updateDimensions}
          />
        </div>
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  dims: state.dimensions.dimensions,
  selectedIndexes: state.dimensions.selectedIndexes,
  hoverId: state.dimensions.hoverInfo.hoverId,
});

export const ConnectedPCChartWidget = connect(mapStateToProps)(
  ParallelCoordinatesWidget,
);

export const ConnectedPCChartBuilder = PCChartStateBuilder(
  "Parallel Coordinates Chart",
);
