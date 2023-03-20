/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import ExperimentEndpoint from "../../server/endpoint";
import Redirect from "../../../../net/redirect";
import {JSON_OBJECT_DENY_LIST} from "../../../../component/code_generator/base";
import {recursivelyOmitKeys} from "../../../../utils";

const DEFAULT_CHUNK_SIZE = 1000;

export default class ExperimentCopyEndpoint extends ExperimentEndpoint {
  get entrypoint() {
    return null;
  }

  parseParams(req) {
    const experiment = req.matchedExperiment;
    const clientId = req.loginState.clientId;
    const includeObservations = req.body.include_observations === "on";
    const chunkSize = req.configBroker.get(
      "features.maxObservationsCreateCount",
      DEFAULT_CHUNK_SIZE,
    );

    if (!clientId) {
      return Promise.reject(new Redirect("/user/info"));
    } else if (req.method === "POST") {
      const uncopiedExperimentKeys = [
        "progress",
        "client",
        "state",
        "user",
        "development",
        "metric",
      ];

      const params = recursivelyOmitKeys(
        _.omit(experiment, uncopiedExperimentKeys),
        JSON_OBJECT_DENY_LIST,
      );
      if (params.name.length > 45) {
        params.name = `${params.name.substring(0, 42)}... Copy`;
      } else {
        params.name += " Copy";
      }

      _.each(params.metrics, (m) => {
        delete m.object;
      });

      _.each(params.parameters, (p) => {
        if (p.grid) {
          delete p.bounds;
        }
      });

      return this.validateProject(clientId, experiment)
        .then((projectId) =>
          this.services.promiseApiClient
            .clients(clientId)
            .experiments()
            .create(_.extend({}, params, {project: projectId})),
        )
        .then((newExperiment) =>
          (includeObservations
            ? this.services.promiseApiClient
                .experiments(experiment.id)
                .observations()
                .exhaustivelyPage()
                .then((observations) =>
                  this.copyObservations(
                    observations.reverse(),
                    newExperiment,
                    chunkSize,
                  ),
                )
            : Promise.resolve()
          ).then(() => {
            throw new Redirect(`/experiment/${newExperiment.id}/properties`);
          }),
        );
    } else {
      return Promise.reject(
        new Redirect(`/experiment/${experiment.id}/properties`),
      );
    }
  }

  validateProject(clientId, experiment) {
    if (experiment.client === clientId) {
      return Promise.resolve(experiment.project);
    } else if (experiment.project) {
      // When copying an experiment to a new client, the project may not exist.
      return this.services.promiseApiClient
        .clients(clientId)
        .projects(experiment.project)
        .fetch()
        .then((project) => project.id)
        .catch((err) => {
          if (_.contains([404], err.status)) {
            return Promise.resolve(null);
          } else {
            return Promise.reject(err);
          }
        });
    } else {
      return Promise.resolve(null);
    }
  }

  copyObservations(allObservations, toExperiment, chunkSize) {
    if (_.isEmpty(allObservations)) {
      return Promise.resolve();
    } else {
      const observations = _.head(allObservations, chunkSize).reverse();
      const rest = _.tail(allObservations, chunkSize);
      const hasValues = _.any(observations, (o) => o.values);
      const uncopiedObservationKeys = [
        "id",
        "object",
        "experiment",
        "created",
        "suggestion",
      ].concat(hasValues ? ["value", "value_stddev"] : ["values"]);
      const paramsList = _.map(observations, (o) => {
        const cleaned = _.omit(o, ...uncopiedObservationKeys);
        cleaned.values =
          cleaned.values && _.map(cleaned.values, (v) => _.omit(v, "object"));
        return cleaned;
      }).reverse();
      const observationsJson = {
        observations: paramsList,
        no_optimize: true,
      };
      return this.services.promiseApiClient
        .experiments(toExperiment.id)
        .observations("batch")
        .create(observationsJson)
        .then(() => this.copyObservations(rest, toExperiment, chunkSize));
    }
  }
}
