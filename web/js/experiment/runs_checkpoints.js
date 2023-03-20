/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./runs_checkpoints.less";

import _ from "underscore";
import React from "react";

import Component from "../react/component";
import Loading from "../component/loading";
import MpmCheckpointsChart from "../chart/mpm_checkpoints_chart";
import ReactChart from "../react_chart/react_chart";

export default class RunsCheckpoints extends Component {
  state = {
    checkpointsByRunId: null,
  };

  unmounted = false;

  componentDidMount() {
    this.services.promiseApiClient
      .trainingRuns(this.props.run.id)
      .checkpoints()
      .exhaustivelyPage()
      .then((checkpoints) =>
        this.unmounted
          ? null
          : this.setState({
              checkpointsByRunId: {[this.props.run.id]: checkpoints.reverse()},
              metricNames: _.chain(checkpoints)
                .pluck("values")
                .flatten()
                .pluck("name")
                .uniq()
                .value(),
            }),
      );
  }

  componentWillUnmount() {
    this.unmounted = true;
  }

  render() {
    const singlePlotHeightPx = 150;
    const paddingPx = 50;
    const chartStyle = {
      height: _.size(this.state.metricNames) * singlePlotHeightPx + paddingPx,
    };
    return (
      <div className="runs-checkpoints-wrapper">
        <Loading
          loading={!this.state.checkpointsByRunId}
          empty={_.chain(this.state.checkpointsByRunId)
            .values()
            .flatten()
            .isEmpty()
            .value()}
          emptyMessage={
            /* eslint-disable-line react/jsx-no-useless-fragment */ <></>
          }
        >
          <div className="checkpoints-title field-name">Checkpoints</div>
          <div className="checkpoints-chart" style={chartStyle}>
            <ReactChart
              args={{
                data: [
                  {
                    checkpointsByRunId: this.state.checkpointsByRunId,
                    metricNames: this.state.metricNames,
                    trainingRuns: [this.props.run],
                  },
                ],
                onClickHandler: this.onClick,
                onCheckpointHover: this.onHover,
                onCheckpointUnhover: this.onUnhover,
              }}
              cls={MpmCheckpointsChart}
            />
          </div>
        </Loading>
      </div>
    );
  }
}
