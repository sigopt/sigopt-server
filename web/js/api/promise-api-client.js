/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Service from "../services/base";
import {exhaustivelyPage} from "../net/paging";

class ApiCaller {
  constructor(path, apiRequestor, pathPrefix = "/v1") {
    this._path = path;
    this._apiRequestor = apiRequestor;
    this._pathPrefix = pathPrefix;
  }

  // TODO(SN-1147): Add other resource types as needed
  // TODO(SN-1148): This does not currently verify that the endpoint you are calling is a real endpoint
  aiexperiments = (...ids) => this._subresource("aiexperiments", ids);
  bestAssignments = (...ids) => this._subresource("best_assignments", ids);
  bestPractices = (...ids) => this._subresource("best_practices", ids);
  checkpoints = (...ids) => this._subresource("checkpoints", ids);
  clients = (...ids) => this._subresource("clients", ids);
  experiments = (...ids) => this._subresource("experiments", ids);
  files = (...ids) => this._subresource("files", ids);
  invites = (...ids) => this._subresource("invites", ids);
  hyperparameters = (...ids) => this._subresource("hyperparameters", ids);
  memberships = (...ids) => this._subresource("memberships", ids);
  metricImportances = (...ids) => this._subresource("metric_importances", ids);
  notes = (...ids) => this._subresource("notes", ids);
  observations = (...ids) => this._subresource("observations", ids);
  organizations = (...ids) => this._subresource("organizations", ids);
  pendingPermissions = (...ids) =>
    this._subresource("pending_permissions", ids);
  permissions = (...ids) => this._subresource("permissions", ids);
  projects = (...ids) => this._subresource("projects", ids); // for /v1/clients/X/projects
  queuedSuggestions = (...ids) => this._subresource("queued_suggestions", ids);
  sessions = (...ids) => this._subresource("sessions", ids);
  stoppingCriteria = (...ids) => this._subresource("stopping_criteria", ids);
  suggestions = (...ids) => this._subresource("suggestions", ids);
  tags = (...ids) => this._subresource("tags", ids);
  tokens = (...ids) => this._subresource("tokens", ids);
  trainingRuns = (...ids) => this._subresource("training_runs", ids);
  users = (...ids) => this._subresource("users", ids);
  verifications = (...ids) => this._subresource("verifications", ids);
  webData = (...ids) => this._subresource("web_data", ids);

  _subresource = (name, ids, pathPrefix = "/v1") => {
    if (ids.length > 1) {
      throw Error(`Too many ids received: ${ids}`);
    }
    const idSegment = _.isEmpty(ids) ? "" : `/${ids[0]}`;
    return new ApiCaller(
      `${this._path}/${name}${idSegment}`,
      this._apiRequestor,
      pathPrefix,
    );
  };

  fetch = (params) => this._call("GET", params);
  create = (params) => this._call("POST", params);
  update = (params) => this._call("PUT", params);
  delete = (params) => this._call("DELETE", params);

  // Call this instead of `fetch` to get all the paginated data as a list
  //
  //   promiseApiClient.clients(1).experiments().exhaustivelyPage() === [{"object": "experiment", ...}, ...]
  //
  // We do not match the Python client's `iterate_pages` here because they have different semantics.
  // The Python client's is a lazy iterator, whereas this eagerly consumes all the content and matches the
  // `exhaustivelyPage` function from net/paging.js
  exhaustivelyPage = (params) =>
    new Promise((s, e) => {
      exhaustivelyPage(
        (paging, s2, e2) =>
          this._apiRequestor.request(
            "GET",
            this._path,
            paging,
            s2,
            e2,
            false,
            this._pathPrefix,
          ),
        {
          success: s,
          error: e,
          params: params,
        },
      );
    });

  _call = (method, params) =>
    new Promise((s, e) => {
      this._apiRequestor.request(
        method,
        this._path,
        params || {},
        s,
        e,
        false,
        this._pathPrefix,
      );
    });
}

/**
 * Calls API methods.
 *
 * Calling format is similar to the python API client, except API calls return a Promise.
 *
 * services.promiseApiClient.clients(1).experiments({state: 'active'}).fetch()
 *   .then(success, error)
 */
export default class PromiseApiClient extends Service {
  constructor(services, options = {}, caller = null) {
    super(services, options);

    this._caller = caller || new ApiCaller("", this.services.apiRequestor);

    // Bind endpoint names from the ApiCaller to this object, so that callers can write
    // services.promiseApiClient.clients(...), etc.
    const resourceNames = _.functions(this._caller);
    _.each(resourceNames, (resourceName) => {
      this[resourceName] = this._caller[resourceName];
    });
  }

  withApiToken(token) {
    const newCaller = new ApiCaller(
      "",
      this.services.apiRequestor.withApiToken(token),
    );
    return new PromiseApiClient(this._services, this._options, newCaller);
  }
}
