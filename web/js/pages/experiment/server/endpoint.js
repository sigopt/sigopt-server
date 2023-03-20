/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../../server/endpoint/loggedin";
import Redirect from "../../../net/redirect";
import ui from "../../../experiment/ui";
import {ExperimentStates} from "../../../experiment/constants";

export default class ExperimentEndpoint extends LoggedInReactEndpoint {
  get allowGuest() {
    return true;
  }

  pageNamePrefix(req) {
    return req.matchedExperiment.name;
  }

  canModifyExperiment(experiment, user, currentPermission, isGuest) {
    return Boolean(
      !isGuest &&
        experiment.state !== ExperimentStates.DELETED &&
        user &&
        currentPermission &&
        currentPermission.can_write,
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
    const isAiExperiment = ui.isAiExperiment(req.matchedExperiment);
    const isCoreRoute = req.originalUrl.includes("/experiment/");

    if (isAiExperiment && isCoreRoute) {
      const aiURL = req.originalUrl.replace("/experiment/", "/aiexperiment/");
      return Promise.reject(new Redirect(aiURL));
    }

    const isGuest =
      req.apiTokenDetail && req.apiTokenDetail.token_type === "guest";
    const isGettingStarted =
      isGuest && !req.apiTokenDetail.user && req.apiTokenDetail.all_experiments;
    return this.getPermissions(req, isGuest).then((userPermissions) => {
      const currentPermission = _.find(
        userPermissions,
        (r) => r.client.id === req.loginState.clientId,
      );
      const hasSharePermission = currentPermission
        ? currentPermission.can_write
        : false;
      const sharingEnabled = req.configBroker.get("features.shareLinks", true);
      const canShare = hasSharePermission && sharingEnabled;

      return super.getParams(req).then((params) =>
        _.extend({}, params, {
          canEdit: this.canModifyExperiment(
            req.matchedExperiment,
            req.currentUser,
            currentPermission,
            isGuest,
          ),
          canShare,
          experiment: req.matchedExperiment,
          isAiExperiment: req.isAiExperiment,
          isGettingStarted: isGettingStarted,
          isGuest: isGuest,
          legacyApiClient: req.services.legacyApiClient,
          loginState: req.loginState,
          path: req.path,
          promiseApiClient: req.services.promiseApiClient,
          user: req.currentUser,
        }),
      );
    });
  }

  _fetchProject(experiment) {
    if (experiment && experiment.project) {
      return this.services.promiseApiClient
        .clients(experiment.client)
        .projects(experiment.project)
        .fetch()
        .catch((e) =>
          _.contains([403, 404], e.status)
            ? Promise.resolve(null)
            : Promise.reject(e),
        );
    } else {
      return Promise.resolve(null);
    }
  }

  _fetchProjects(experiment) {
    if (experiment && experiment.client) {
      return this.services.promiseApiClient
        .clients(experiment.client)
        .projects()
        .exhaustivelyPage()
        .then((projects) => {
          const currentProject = _.find(
            projects,
            ({id}) => id === experiment.project,
          );
          return {currentProject, projects};
        })
        .catch((e) => {
          if (_.contains([403, 404], e.status)) {
            return this._fetchProject(experiment).then((currentProject) => ({
              currentProject,
              projects: null,
            }));
          } else {
            return Promise.reject(e);
          }
        });
    } else {
      return Promise.resolve({currentProject: null, projects: []});
    }
  }

  _fetchClient(clientId) {
    if (clientId) {
      return this.services.promiseApiClient
        .clients(clientId)
        .fetch()
        .catch((e) =>
          _.contains([403, 404], e.status)
            ? Promise.resolve(null)
            : Promise.reject(e),
        );
    } else {
      return Promise.resolve(null);
    }
  }

  _fetchCreator(experiment) {
    if (experiment && experiment.user) {
      return this.services.promiseApiClient
        .users(experiment.user)
        .fetch()
        .catch((e) =>
          _.contains([403, 404], e.status)
            ? Promise.resolve(null)
            : Promise.reject(e),
        );
    } else {
      return Promise.resolve(null);
    }
  }
}
