/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import Chart from "../../../chart/chart";
import ReactChart from "../../../react_chart/react_chart";
import RunPageSection from "./section";
import TableContent from "./table";
import defaultLayout from "../../../react_chart/layout";
import {DOCS_URL} from "../../../net/constant";
import {GetTrainingRunIntegrationType} from "../utils";

function SortFeatureImportances(obj) {
  return _.chain(obj)
    .pairs()
    .sort(([, v0], [, v1]) => v1 - v0)
    .value();
}

const TOP_K = 20;

function FeatureImportancesReference(run) {
  const integration = GetTrainingRunIntegrationType(run);
  if (integration === "XGBoost") {
    return `${DOCS_URL}/ai-module-api-references/xgboost/xgboost_run#feature-importances`;
  }
  return null;
}

class FeatureImportanceBarChart extends Chart {
  getChartArgs({featureImportances}) {
    const [features, scores] = _.unzip(
      SortFeatureImportances(featureImportances.scores)
        .slice(0, TOP_K)
        .reverse(),
    );
    const chunked_features = _.map(features, (name) =>
      name.length <= 20 ? name : `${name.slice(0, 10)}...${name.slice(-10)}`,
    );
    const n = chunked_features.length;
    let layout = {
      overflow: "scroll",
      xaxis: {
        title: {
          text: "Importance",
        },
        zeroline: false,
      },
      yaxis: {
        automargin: true,
        title: {
          text: "Feature",
        },
        tickmode: "linear",
        range: [_.max([-0.5, n - 0.5 - TOP_K]), n - 0.5],
        rangeslider: {
          visible: true,
        },
      },
    };

    layout = _.extend({}, defaultLayout, layout);
    return {
      data: [{x: scores, y: chunked_features, type: "bar", orientation: "h"}],
      layout: layout,
    };
  }
}

const Content = ({trainingRun}) => {
  const featureImportances = trainingRun.sys_metadata.feature_importances;
  const reference = FeatureImportancesReference(trainingRun);
  const feature_num = _.size(featureImportances.scores);
  return (
    <>
      {reference && (
        <p style={{"text-align": "right"}}>
          <a href={reference}>Learn more about feature importances</a>
        </p>
      )}

      {feature_num > TOP_K && (
        <div className="alert alert-success">
          {" "}
          Only top {TOP_K} features are displayed in the bar chart; total{" "}
          {feature_num} features are logged and are listed in the table below.
        </div>
      )}
      <ReactChart
        args={{data: [{featureImportances}]}}
        cls={FeatureImportanceBarChart}
      />
      <div>
        <TableContent headers={["Feature", "Importance"]} scrollable={false} />
      </div>
      <div style={{"max-height": "300px", "overflow-y": "scroll"}}>
        <TableContent
          content={SortFeatureImportances(featureImportances.scores)}
          scrollable={true}
        />
      </div>
    </>
  );
};

export default (props) => (
  <RunPageSection
    empty={!props.trainingRun.sys_metadata.feature_importances}
    Content={Content}
    title="Feature Importances"
    {...props}
  />
);
