/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import Component from "../../../react/component";
import Loading from "../../../component/loading";
import RunPageSection from "./section";
import forceRemountOnUpdate from "../../../react/force-remount";
import ui from "../../../experiment/ui";
import {DOCS_URL} from "../../../net/constant";
import {GetTrainingRunIntegrationType} from "../utils";
import {HYPEROPT, XGBOOST} from "../constants";
import {TableCard} from "../../../experiment/tables";

const experimentRawTypeToNiceType = {
  development: "Development",
  grid: "Grid Search",
  offline: "Intelligent Optimization",
  random: "Random Search",
};

const OptimizationTable = ({experiment}) => (
  <TableCard>
    <tbody>
      <tr>
        <td>Optimization Type</td>
        <td>{experimentRawTypeToNiceType[experiment.type] || "Unknown"}</td>
      </tr>
      <tr>
        <td>Experiment Name</td>
        <td>
          <a href={ui.getExperimentUrl(experiment)}>{experiment.name}</a>
        </td>
      </tr>
      <tr>
        <td>Experiment ID</td>
        <td>{experiment.id}</td>
      </tr>
    </tbody>
  </TableCard>
);

const Content = forceRemountOnUpdate(
  class OptimizationContent extends Component {
    state = {experiment: null};

    componentDidMount() {
      this.services.promiseApiClient
        .experiments(this.props.trainingRun.experiment)
        .fetch()
        .then((experiment) => this.setState({experiment}));
    }

    render() {
      const {experiment} = this.state;
      if (!experiment) {
        return <Loading loading={true} />;
      }
      return <OptimizationTable experiment={experiment} />;
    }
  },
);

const EmptyMessage = () => (
  <p>
    This run was not optimized. Create a hyperparameter optimization experiment
    with <code>sigopt optimize python model.py</code> in the terminal, or use
    the <code>%%optimize</code> magic command in a notebook.
  </p>
);

const XGBoostEmptyMessage = () => (
  <p>
    This run was not optimized. You can create a hyperparameter optimization
    experiment for XGBoost model with <code>sigopt.xgboost.experiment</code>.
    See{" "}
    <a href={`${DOCS_URL}/ai-module-api-references/xgboost/xgboost_experiment`}>
      doc
    </a>{" "}
    for more information.
  </p>
);

const HyperoptEmptyMessage = () => (
  <p>
    This run was optimized by Hyperopt. See{" "}
    <a href={`${DOCS_URL}/ai-module-api-reference/hyperopt`}>doc</a> for more
    information.
  </p>
);

const GetEmptyMessage = (props) => {
  const integration = GetTrainingRunIntegrationType(props.trainingRun);
  if (integration === XGBOOST) {
    return XGBoostEmptyMessage;
  }
  if (integration === HYPEROPT) {
    return HyperoptEmptyMessage;
  }
  return EmptyMessage;
};

export default (props) => {
  return (
    <RunPageSection
      Content={Content}
      EmptyMessage={GetEmptyMessage(props)}
      empty={!props.trainingRun.experiment}
      title="Optimization"
      {...props}
    />
  );
};
