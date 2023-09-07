/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../../server/endpoint/loggedin";

export default class TrainingRunEndpoint extends LoggedInReactEndpoint {
  get allowGuest() {
    return true;
  }

  pageNamePrefix(req) {
    return req.matchedTrainingRun.name;
  }

  canModifyRun(run, currentPermission, isGuest) {
    return Boolean(
      !isGuest &&
        currentPermission &&
        currentPermission.client.id === run.client &&
        currentPermission.can_write,
    );
  }

  getProject(req) {
    return this.services.promiseApiClient
      .clients(req.matchedTrainingRun.client)
      .projects(req.matchedTrainingRun.project)
      .fetch()
      .catch((err) =>
        _.contains([403, 404], err.status)
          ? Promise.resolve(null)
          : Promise.reject(err),
      );
  }

  getUser(req) {
    // TODO: Can short-circuit in the common case where the training run was created by the current user
    return this.services.promiseApiClient
      .users(req.matchedTrainingRun.user)
      .fetch()
      .catch((err) =>
        _.contains([403, 404], err.status)
          ? Promise.resolve(null)
          : Promise.reject(err),
      );
  }

  getTags(req) {
    return this.services.promiseApiClient
      .clients(req.matchedTrainingRun.client)
      .tags()
      .exhaustivelyPage()
      .then((tags) => Promise.resolve(_.indexBy(tags, "id")))
      .catch((err) =>
        _.contains([403, 404], err.status)
          ? Promise.resolve(null)
          : Promise.reject(err),
      );
  }

  getPermissions(req, isGuest) {
    if (isGuest) {
      return Promise.resolve([]);
    }
    return this.services.promiseApiClient
      .users(req.loginState.userId)
      .permissions()
      .exhaustivelyPage();
  }

  getParams(req) {
    const isGuest =
      req.apiTokenDetail && req.apiTokenDetail.token_type === "guest";
    return super.getParams(req).then((params) =>
      Promise.all([
        this.getUser(req),
        this.getProject(req),
        this.getTags(req),
        this.getPermissions(req, isGuest),
      ]).then(([user, project, tags, permissions]) => {
        const currentPermission = _.find(
          permissions,
          (r) => r.client.id === req.loginState.clientId,
        );
        return _.extend({}, params, {
          canEdit: this.canModifyRun(
            req.matchedTrainingRun,
            currentPermission,
            isGuest,
          ),
          loginState: req.loginState,
          promiseApiClient: this.services.promiseApiClient,
          project,
          showBreadcrumbs: !isGuest,
          tags,
          trainingRun: req.matchedTrainingRun,
          user,
        });
      }),
    );
  }
}
