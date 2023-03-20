/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {get as lodashGet} from "lodash";

import {isDefinedAndNotNull} from "../utils";

const filterDefaultParams = (runs, definedFields) => {
  const ASSIGNMENT_PREFIX = "assignments.";
  const assignments = _.map(
    _.filter(definedFields, (item) => item.key.startsWith(ASSIGNMENT_PREFIX)),
    (item) => item.key.slice(ASSIGNMENT_PREFIX.length),
  );
  const showSet = new Set();
  runs.forEach((run) => {
    assignments.forEach((name) => {
      const value = lodashGet(run, `assignments.${name}`, null);
      if (value !== null) {
        const source = lodashGet(run, `assignments_meta.${name}.source`, null);
        if (
          !source ||
          lodashGet(run, `assignments_sources.${source}.default_show`, true)
        ) {
          showSet.add(name);
        }
      }
    });
  });

  return _.filter(
    definedFields,
    (item) =>
      !item.key.startsWith(ASSIGNMENT_PREFIX) ||
      showSet.has(item.key.slice(ASSIGNMENT_PREFIX.length)),
  );
};

export default function fetchRuns(
  promiseApiClient,
  project,
  experiment = null,
  needFilterDefaultParams = true,
  organizationId = null,
  excludeArchivedRuns = false,
) {
  let runsApi = null;
  let client_defined = true;
  if (isDefinedAndNotNull(organizationId)) {
    // if org_id, it takes precedence, otherwise default to proj/client
    runsApi = promiseApiClient.organizations(organizationId).trainingRuns();
    client_defined = false;
  } else {
    runsApi = promiseApiClient
      .clients(project.client)
      .projects(project.id)
      .trainingRuns();
  }

  let filters = [];
  if (isDefinedAndNotNull(experiment)) {
    filters.push({field: "experiment", operator: "==", value: experiment});
  }
  if (excludeArchivedRuns) {
    filters.push({
      field: "deleted",
      operator: "==",
      value: false,
    });
  }
  filters = JSON.stringify(filters);

  const promise_array = [
    runsApi
      .fetch({limit: 0, filters})
      .then((pagination) => pagination.defined_fields),
    runsApi.exhaustivelyPage({filters}),
  ];
  if (client_defined) {
    promise_array.push(
      promiseApiClient
        .clients(project.client)
        .tags()
        .exhaustivelyPage()
        .then((tags) => _.indexBy(tags, "id")),
    );
  }

  let promise = Promise.all(promise_array);

  if (needFilterDefaultParams) {
    promise = promise.then(([definedFields, runs, tags]) => [
      filterDefaultParams(runs, definedFields),
      runs,
      tags,
    ]);
  }

  return promise.then(([definedFields, runs, tags]) =>
    Promise.resolve({
      definedFields,
      runs,
      tags,
    }),
  );
}
