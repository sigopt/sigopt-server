/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ExperimentImprovementChart from "./chart";
import ExperimentImprovementTitle from "./title";
import Loading from "../../component/loading";
import StagnationInfo from "./stagnation_info";
import schemas from "../../react/schemas";
import ui from "../../experiment/ui";
import {isDefinedAndNotNull} from "../../utils";

class ExperimentImprovement extends React.Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    metric: PropTypes.object.isRequired,
    observations: PropTypes.arrayOf(
      schemas.observationRequiresFields(["values"]),
    ),
    onClickHandler: PropTypes.func,
    stoppingCriteria: PropTypes.object,
  };

  render() {
    const metric =
      this.props.metric || ui.optimizedMetrics(this.props.experiment)[0];
    return (
      <div className="experiment-improvement">
        <ExperimentImprovementTitle metric={metric} />
        <Loading
          loading={!isDefinedAndNotNull(this.props.observations)}
          empty={_.isEmpty(this.props.observations)}
        >
          <>
            <StagnationInfo stoppingCriteria={this.props.stoppingCriteria} />
            <ExperimentImprovementChart
              metric={metric}
              experiment={this.props.experiment}
              observations={this.props.observations || []}
              onClickHandler={this.props.onClickHandler}
            />
          </>
        </Loading>
      </div>
    );
  }
}

export default ExperimentImprovement;
