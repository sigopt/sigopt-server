/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import {connect} from "react-redux";

import Component from "../../../../../react/component";
import Loading from "../../../../../component/loading";
import MpmCheckpointsChart from "../../../../../chart/mpm_checkpoints_chart";
import ReactChart from "../../../../../react_chart/react_chart";
import makeMouseHover from "../../../../../component/mouse_hover_hoc";
import {isUndefinedOrNull} from "../../../../../utils";
import {setHoverInfo} from "../../../state/dimensions_slice";

const CheckpointsChartWidget = makeMouseHover(
  class CheckpointsChartWidget extends Component {
    reactChart = React.createRef();

    componentDidMount() {
      this.componentDidUpdate({});
    }

    componentDidUpdate(prevProps) {
      const chart = this.reactChart.current;
      if (!chart) {
        return;
      }

      const {hoverInfo, indexIdMap, mouseHovered} = this.props;
      if (
        mouseHovered &&
        hoverInfo &&
        !_.isEqual(prevProps.hoverInfo, hoverInfo)
      ) {
        const {checkpointIndex, runIndex} = hoverInfo;
        chart.chart.hoverTraces(indexIdMap[runIndex], checkpointIndex);
      }
    }

    onHover = (runId, checkpointIndex) => {
      this.props.setHoverInfo({
        runId: runId,
        checkpointIndex: checkpointIndex,
      });
    };

    performInitialResize = () => {
      const runsIdsToPlot = this.props.widget.state.runIds;

      const metricNames = _.chain(runsIdsToPlot)
        .map((id) =>
          _.chain(this.props.checkpoints[id])
            .pluck("values")
            .flatten()
            .pluck("name")
            .value(),
        )
        .flatten()
        .filter()
        .uniq()
        .value();

      const height = metricNames.length * 2 + 1;
      this.props.updateWidget((widget) => {
        widget.layout.h = Math.max(height, widget.layout.minH);
      });
    };

    render() {
      if (isUndefinedOrNull(this.props.checkpoints)) {
        return <Loading loading={true} />;
      }

      let runsIdsToPlot = _.values(this.props.indexIdMap);
      if (!this.props.widget.state.plotAllRuns) {
        runsIdsToPlot = this.props.widget.state.runIds;
      }

      const trainingRunsToPlot = _.filter(this.props.runsById, (run) =>
        _.contains(runsIdsToPlot, run.id),
      );

      const metricNames = _.chain(runsIdsToPlot)
        .map((id) =>
          _.chain(this.props.checkpoints[id])
            .pluck("values")
            .flatten()
            .pluck("name")
            .value(),
        )
        .flatten()
        .filter()
        .uniq()
        .value();

      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            width: "100%",
          }}
        >
          <ReactChart
            args={{
              data: [
                {
                  checkpointsByRunId: this.props.checkpoints,
                  metricNames,
                  trainingRuns: trainingRunsToPlot,
                },
              ],
              onClickHandler: this.onClick,
              onCheckpointHover: this.onHover,
              onCheckpointUnhover: this.onUnhover,
            }}
            cls={MpmCheckpointsChart}
            ref={this.reactChart}
          />
        </div>
      );
    }
  },
);

const mapStateToProps = (state) => ({
  checkpoints: state.dimensions.checkpointsByRunId,
  hoverId: state.dimensions.hoverInfo,
  dims: state.dimensions.dimensions,
  hoverInfo: state.dimensions.hoverInfo,
  checkpointIndex: state.dimensions.checkpointIndex,
  indexIdMap: state.dimensions.indexIdMap,
  runsById: state.dimensions.runsById,
});

const mapDispatchToProps = {setHoverInfo};

export const ConnectedCheckpointsChartWidget = connect(
  mapStateToProps,
  mapDispatchToProps,
)(CheckpointsChartWidget);

export const ConnectedCheckpointsChartBuilder = {
  layout: {w: 2, h: 8, minW: 1, minH: 5},
  type: "CheckpointsChart",
  state: {title: "Checkpoints Chart"},
};
