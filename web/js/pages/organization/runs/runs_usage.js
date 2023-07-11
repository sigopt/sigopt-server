/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ReactChart from "../../../react_chart/react_chart";
import Spinner from "../../../component/spinner";
import UsageChart from "../../../chart/usage_chart";
import layout from "../../../react_chart/layout";
import schemas from "../../../react/schemas";
import {calculateLastNPeriods} from "../../../time";
import {createTrainingRunFilters} from "./lib";

const NUM_PERIODS_TO_DISPLAY = 6;

class RunsUsage extends React.Component {
  static propTypes = {
    currentPeriodEnd: PropTypes.number.isRequired,
    organization: schemas.Organization.isRequired,
    promiseApiClient: PropTypes.object.isRequired,
  };

  state = {
    history: {},
  };

  componentDidMount() {
    _.each(
      calculateLastNPeriods(
        NUM_PERIODS_TO_DISPLAY,
        this.props.currentPeriodEnd,
      ),
      (p) => {
        const filterArray = createTrainingRunFilters(
          null,
          Math.floor(p.start),
          Math.floor(p.end),
          true,
        );
        this.props.promiseApiClient
          .organizations(this.props.organization.id)
          .trainingRuns()
          .fetch({
            filters: JSON.stringify(filterArray),
            limit: 0,
          })
          .then((data) => {
            this.setState(function (prevState) {
              const historyData = _.extend({count: data.count}, p);
              const newHistory = _.extend(
                {[p.index]: historyData},
                prevState.history,
              );
              return {history: newHistory};
            });
          });
      },
    );
  }

  render() {
    const loading =
      _.keys(this.state.history).length !== NUM_PERIODS_TO_DISPLAY;
    layout.xaxis.fixedrange = true;
    layout.yaxis.fixedrange = true;
    return (
      <div>
        <h3>{NUM_PERIODS_TO_DISPLAY}-Month Usage History</h3>
        {loading ? <Spinner /> : null}
        {!loading && (
          <ReactChart
            args={{
              data: [this.state.history],
              layout: layout,
              is_runs: true,
            }}
            cls={UsageChart}
          />
        )}
      </div>
    );
  }
}

export default RunsUsage;
