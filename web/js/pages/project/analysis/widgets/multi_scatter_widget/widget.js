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

import Component from "../../../../../react/component";
import {
  ColorLegend,
  GRADIENT_TYPES,
  createColorDimensionGradient,
  createColorDimensionWithSelect,
} from "../../lib/color_dimension";
import {getPossibleDimensions} from "../../lib/dimensions";
import {isDefinedAndNotNull} from "../../../../../utils";
import {make2dScatterJson} from "./plotly_json_builder";
import {
  setHoverInfo,
  setSelectedIndexes,
} from "../../../state/dimensions_slice";

class MultiScatterPlot extends Component {
  constructor(props) {
    super(props);

    const graphDivID = Math.random().toString();

    this.state = {
      graphDivID,
      chart: null,
    };
  }

  componentDidMount() {
    const node = ReactDOM.findDOMNode(this);
    node.addEventListener("resize", () => {
      if (this.state.chart) {
        Plotly.Plots.resize(this.state.chart);
      }
    });
    if (this.props.widget.state) {
      _.defer(() => this.drawChart());
    }
  }

  // TODO convert to reactchart
  componentDidUpdate(prevProps) {
    if (!this.props.widget.state) {
      return;
    }
    if (
      prevProps.widget.state === null ||
      this.props.widget.state.xDimKeys !== prevProps.widget.state.xDimKeys
    ) {
      this.drawChart();
    }

    if (this.props.dims !== prevProps.dims) {
      this.drawChart();
    }
    if (
      this.props.selectedIndexes !== prevProps.selectedIndexes &&
      this.state.chart
    ) {
      Plotly.restyle(this.state.chart, {selectedIndexes: [null]});
      this.drawChart();
    }
    if (this.state.chart && isDefinedAndNotNull(this.props.hoverIndex)) {
      this.hoverAll();
    }
  }

  clearHover() {
    Plotly.Fx.hover(this.state.chart, {});
  }

  hoverAll() {
    if (!this.state.subPlots) {
      return;
    }
    const pointNumber = this.props.hoverIndex;
    const numCharts =
      this.props.widget.state.xDimKeys.length *
      this.props.widget.state.yDimKeys.length;
    const points = _.map(new Array(numCharts), (unused, i) => ({
      pointNumber,
      curveNumber: i,
    }));
    const plots = this.state.subPlots;

    // Can be issue with hover after editing since plots are different
    // Race condition between drawChart/hoverAll running.
    // Should be able to figure out something a bit nicer.
    try {
      Plotly.Fx.hover(this.state.chart, points, plots);
    } catch (e) {}
  }

  drawChart() {
    const graphDiv = document.getElementById(this.state.graphDivID);

    const axisData = [];
    const axisLayouts = {};
    const {dims: xDims, invalidDims: invalidXDims} = getPossibleDimensions(
      this.props.dims,
      this.props.widget.state.xDimKeys,
    );
    const {dims: yDims, invalidDims: invalidYDims} = getPossibleDimensions(
      this.props.dims,
      this.props.widget.state.yDimKeys,
    );

    const invalidDims = invalidXDims.concat(invalidYDims);

    let graphColors = {color: "#6699ff"};
    const shouldHighlightPoints = this.props.selectedIndexes.length > 0;
    const colorState = this.props.widget.state.colorState;

    if (shouldHighlightPoints) {
      graphColors = createColorDimensionWithSelect(
        xDims[0].values.length,
        this.props.selectedIndexes,
      );
    } else if (colorState) {
      try {
        graphColors = createColorDimensionGradient(this.props.dims, colorState);
        this.setState({legendData: graphColors.legendData});
      } catch (err) {
        invalidDims.push(colorState.key);
      }
    }

    if (invalidDims.length > 0) {
      this.props.updateWidget((state) => {
        state.warning = `Due to changes the following dimensions are no longer plottable:
        ${invalidDims.join(", ")}.`;
      });
    } else {
      this.props.updateWidget((state) => {
        state.warning = null;
      });
    }

    let xAxisNumber = 1;
    let yAxisNumber = 1;
    for (const yDim of yDims) {
      xAxisNumber = 1;
      for (const xDim of xDims) {
        const {data, layout} = make2dScatterJson(
          xDim,
          yDim,
          xAxisNumber,
          yAxisNumber,
        );

        data.marker.color = graphColors.color;
        data.marker.colorscale = graphColors.colorscale;
        data.colorbar = {title: "test"};
        data.marker.cmin = graphColors.cmin;
        data.marker.cmax = graphColors.cmax;
        data.marker.showscale = graphColors.showscale;

        axisData.push(data);
        _.extend(axisLayouts, layout);
        xAxisNumber += 1;
      }
      yAxisNumber += 1;
    }

    const baselayout = {
      showlegend: false,
      uirevision: "true",
      dragmode: "select",
      hovermode: "closest",
      margin: {t: 10},
      grid: {
        columns: xDims.length,
        rows: yDims.length,
      },
    };

    const layout = _.extend(baselayout, axisLayouts);
    const subPlots = _.map(axisData, (axis) =>
      (axis.xaxis + axis.yaxis).replace(/1/gu, ""),
    );
    this.setState({subPlots});

    if (this.state.chart) {
      Plotly.react(graphDiv, axisData, layout);
    } else {
      Plotly.newPlot(graphDiv, axisData, layout, {
        displayModeBar: false,
        responsive: true,
      });

      graphDiv.on("plotly_selected", (eventData) => {
        if (eventData) {
          const pointIndexes = _.pluck(eventData.points, "pointIndex");
          this.props.setSelectedIndexes(pointIndexes);
        }
      });

      graphDiv.on("plotly_hover", (data) => {
        if (data && data.points && data.points[0]) {
          this.props.setHoverInfo({runIndex: data.points[0].pointIndex});
        }
      });

      graphDiv.on("plotly_click", (data) => {
        if (
          data &&
          data.points &&
          data.points[0] &&
          data.points[0].pointIndex
        ) {
          const runId = this.props.indexIdMap[data.points[0].pointIndex];
          this.services.navigator.navigateInNewTab(`/run/${runId}`);
        }
      });

      this.setState({chart: graphDiv});
    }
  }

  clearSelection = () => {
    this.props.setSelectedIndexes([]);
    Plotly.restyle(this.state.chart, {selectedpoints: [null]});
  };

  render() {
    const showFixedGradientLegend =
      this.props.widget.state.colorState &&
      this.props.widget.state.colorState.gradientType === GRADIENT_TYPES.FIXED;

    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          onClick={this.clearSelection}
          id={this.state.graphDivID}
          className="flex-grow full-width"
        />
        {showFixedGradientLegend ? (
          <div style={{height: 30}}>
            {this.state.legendData ? (
              <ColorLegend
                legendData={this.state.legendData}
                flexDirection="row"
              />
            ) : null}
          </div>
        ) : null}
      </div>
    );
  }
}

const mapStateToProps = (state) => ({
  dims: state.dimensions.dimensions,
  selectedIndexes: state.dimensions.selectedIndexes,
  hoverIndex: state.dimensions.hoverInfo.runIndex,
  indexIdMap: state.dimensions.indexIdMap,
});

const mapDispatchToProps = {setSelectedIndexes, setHoverInfo};

export const MultiScatterWidget = connect(
  mapStateToProps,
  mapDispatchToProps,
)(MultiScatterPlot);
