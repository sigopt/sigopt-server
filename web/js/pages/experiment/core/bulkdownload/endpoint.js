/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import csvWriter from "csv-stringify";
import streamArray from "stream-array";

import Endpoint from "../../../../server/endpoint/base";
import Response from "../../../../net/response";
import StreamResponseSerializer from "../../../../server/serializer/stream";
import ui from "../../../../experiment/ui";
import {excelSanitize} from "../../csvutils";
import {isDefinedAndNotNull} from "../../../../utils";

export default class ExperimentHistoryDownloadEndpoint extends Endpoint {
  constructor() {
    super();
    this.timeout = 30;
  }

  parseParams(req) {
    const experiment = req.matchedExperiment;
    const parameters = experiment.parameters;
    const metrics = experiment.metrics;

    return this.services.promiseApiClient
      .experiments(experiment.id)
      .observations()
      .exhaustivelyPage()
      .then((observations) => {
        const metadataKeys = ui.getMetadataKeys(observations);

        const shallowFlatten = (list) => _.flatten(list, true);

        const orderedAccessors = _.map(parameters, (p) => [
          `parameter-${p.name}`,
          (o, ra) => ra[p.name],
        ])
          .concat(
            _.map(experiment.conditionals, (c) => [
              `conditional-${c.name}`,
              (o, ra) => ra[c.name],
            ]),
          )
          .concat(
            shallowFlatten(
              _.map(metrics, (m) => [
                [
                  m.name ? `value-${m.name}` : "value",
                  (o) => {
                    const value = _.find(
                      o.values,
                      (v) => v.name === m.name || (!m.name && !v.name),
                    );
                    return this.asString(value && value.value);
                  },
                ],
                [
                  m.name ? `value_stddev-${m.name}` : "value_stddev",
                  (o) => {
                    const value = _.find(
                      o.values,
                      (v) => v.name === m.name || (!m.name && !v.name),
                    );
                    return this.asString(value && value.value_stddev);
                  },
                ],
              ]),
            ),
          )
          .concat(
            experiment.tasks
              ? [
                  ["task_name", (o) => o.task.name],
                  ["task_cost", (o) => this.asString(o.task.cost)],
                ]
              : [],
          )
          .concat([
            ["failed", (o) => this.asString(o.failed)],
            ["created", (o) => this.asString(o.created)],
          ])
          .concat(
            _.map(metadataKeys, (m) => [
              `metadata-${m}`,
              (o) => this.asString((o.metadata || {})[m]),
            ]),
          )
          .concat([["id", (o) => this.asString(o.id)]]);

        const data = _.map(observations, (obs) => {
          const renderedAssignments = ui.renderAssignments(
            experiment,
            obs.assignments,
          );
          return _.map(orderedAccessors, (accessor) =>
            accessor[1](obs, renderedAssignments),
          );
        });
        const writer = csvWriter({
          cast: {string: (value) => excelSanitize(value)},
          columns: _.pluck(orderedAccessors, 0),
          header: true,
        });
        return {
          body: streamArray(data).pipe(writer),
          filename: `experiment_${experiment.id}_observations.csv`,
        };
      });
  }

  asString(value) {
    if (isDefinedAndNotNull(value)) {
      return value.toString();
    } else {
      return "";
    }
  }

  // TODO(SN-1161): We could improve this by allowing us to stream the response as it is fetched instead
  // of composing the whole body first
  render(params) {
    return new Response(200, params.body, {
      headers: {
        "Content-Disposition": `attachment; filename="${params.filename}"`,
        "Content-Type": "text/csv",
      },
    });
  }

  serializer() {
    return new StreamResponseSerializer();
  }
}
