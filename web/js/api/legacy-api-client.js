/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {takeWhile} from "lodash";

import Service from "../services/base";
import {isJsObject, isUndefinedOrNull} from "../utils";

class LegacyApiClient extends Service {
  constructor(services, options) {
    super(services, options);

    this.get = (path, params, success, error) =>
      this.services.apiRequestor.request(
        "GET",
        path,
        params,
        success,
        error,
        true,
      );

    this.post = (path, params, success, error) =>
      this.services.apiRequestor.request(
        "POST",
        path,
        params,
        success,
        error,
        true,
      );

    this.put = (path, params, success, error) =>
      this.services.apiRequestor.request(
        "PUT",
        path,
        params,
        success,
        error,
        true,
      );

    this.delete = (path, params, success, error) =>
      this.services.apiRequestor.request(
        "DELETE",
        path,
        params,
        success,
        error,
        true,
      );

    const makeEndpoint = (executor, pathSeed) => {
      const pathCreator = _.isString(pathSeed) ? () => pathSeed : pathSeed;
      const numIds = pathCreator.length;
      return (...args) => {
        const ids = _.take(args, numIds);
        const validIds = _.filter(ids, (f) => _.isString(f) || _.isNumber(f));
        if (validIds.length < ids.length) {
          throw new Error(`Invalid arguments for API call: ${args}`);
        }

        const isParamsObject = (f) => isUndefinedOrNull(f) || isJsObject(f);
        const maybeParams = _.take(
          takeWhile(args.slice(numIds), isParamsObject),
          1,
        );

        const reversedArgs = args.slice().reverse();
        const isHandler = (f) => isUndefinedOrNull(f) || _.isFunction(f);
        const handlers = _.take(
          takeWhile(reversedArgs, isHandler),
          2,
        ).reverse();
        const [success, error] = handlers;

        const composedArgs = ids.concat(maybeParams).concat(handlers);

        if (composedArgs.length !== args.length) {
          throw new Error(`Invalid arguments for API call: ${args}`);
        }

        return executor(
          pathCreator(...ids),
          maybeParams[0] || {},
          success || null,
          error || null,
        );
      };
    };
    const getEndpoint = (pathCreator) => makeEndpoint(this.get, pathCreator);
    const postEndpoint = (pathCreator) => makeEndpoint(this.post, pathCreator);
    const putEndpoint = (pathCreator) => makeEndpoint(this.put, pathCreator);
    const deleteEndpoint = (pathCreator) =>
      makeEndpoint(this.delete, pathCreator);

    /**
     * NOTE: Calling these API methods is deprecated. You should prefer
     * the methods in promise-api-client.js.
     *
     * Definition of all API endpoints.
     * API endpoints are called with 0 or more optional parameters, like so:
     *
     * services.legacyApiClient.endpointName([id1[, id2]], [params], [success[, error]])
     *   (square brackets are not arrays - they indicate parameters that are optional)
     *
     * id1 and id2 represent IDs that are interspersed into the endpoint path, like
     * in /v1/clients/X/experiments
     *
     * params are the parameters passed into the API endpoint
     *
     * success / error are callbacks for if the endpoint succeeds or fails.
     *
     * NOTE: we're declaring all the API endpoints in the constructor here,
     * so that they are all bound to Api. This is to prevent calling them with a
     * useless `this`
     */
    /* eslint-disable max-len */
    this.clientCreate = postEndpoint("/clients");
    this.clientDelete = deleteEndpoint((clientId) => `/clients/${clientId}`);
    this.clientDetail = getEndpoint((clientId) => `/clients/${clientId}`);
    this.clientExperiments = getEndpoint(
      (clientId) => `/clients/${clientId}/experiments`,
    );
    this.clientInviteDelete = deleteEndpoint(
      (clientId) => `/clients/${clientId}/invites`,
    );
    this.clientMerge = putEndpoint((clientId) => `/clients/${clientId}/merge`);
    this.clientPendingPermissions = getEndpoint(
      (clientId) => `/clients/${clientId}/pending_permissions`,
    );
    this.clientPermissions = getEndpoint(
      (clientId) => `/clients/${clientId}/permissions`,
    );
    this.clientTokens = getEndpoint(
      (clientId) => `/clients/${clientId}/tokens`,
    );
    this.clientUpdate = putEndpoint((clientId) => `/clients/${clientId}`);
    this.experimentBestAssignments = getEndpoint(
      (experimentId) => `/experiments/${experimentId}/best_assignments`,
    );
    this.experimentBestPractices = getEndpoint(
      (experimentId) => `/experiments/${experimentId}/best_practices`,
    );
    this.experimentCreate = postEndpoint(
      (clientId) => `/clients/${clientId}/experiments`,
    );
    this.experimentDelete = deleteEndpoint(
      (experimentId) => `/experiments/${experimentId}`,
    );
    this.experimentDetail = getEndpoint(
      (experimentId) => `/experiments/${experimentId}`,
    );
    this.experimentObservations = getEndpoint(
      (experimentId) => `/experiments/${experimentId}/observations`,
    );
    this.experimentSuggestions = getEndpoint(
      (experimentId) => `/experiments/${experimentId}/suggestions`,
    );
    this.experimentUpdate = putEndpoint(
      (experimentId) => `/experiments/${experimentId}`,
    );
    this.forgotPassword = deleteEndpoint("/sessions");
    this.observationsCreate = postEndpoint(
      (experimentId) => `/experiments/${experimentId}/observations`,
    );
    this.observationsCreateMulti = postEndpoint(
      (experimentId) => `/experiments/${experimentId}/observations/batch`,
    );
    this.observationsDelete = deleteEndpoint(
      (experimentId, observationId) =>
        `/experiments/${experimentId}/observations/${observationId}`,
    );
    this.observationsDeleteAll = deleteEndpoint(
      (experimentId) => `/experiments/${experimentId}/observations`,
    );
    this.observationsUpdate = putEndpoint(
      (experimentId, observationId) =>
        `/experiments/${experimentId}/observations/${observationId}`,
    );
    this.organizationClientCreate = postEndpoint(
      (organizationId) => `/organizations/${organizationId}/clients`,
    );
    this.organizationClients = getEndpoint(
      (organizationId) => `/organizations/${organizationId}/clients`,
    );
    this.organizationCreate = postEndpoint("/organizations");
    this.organizationDelete = deleteEndpoint(
      (organizationId) => `/organizations/${organizationId}`,
    );
    this.organizationDetail = getEndpoint(
      (organizationId) => `/organizations/${organizationId}`,
    );
    this.organizationInviteCreate = postEndpoint(
      (organizationId) => `/organizations/${organizationId}/invites`,
    );
    this.organizationInviteDelete = deleteEndpoint(
      (organizationId) => `/organizations/${organizationId}/invites`,
    );
    this.organizationInvites = getEndpoint(
      (organizationId) => `/organizations/${organizationId}/invites`,
    );
    this.organizationMemberships = getEndpoint(
      (organizationId) => `/organizations/${organizationId}/memberships`,
    );
    this.organizationPermissions = getEndpoint(
      (organizationId) => `/organizations/${organizationId}/permissions`,
    );
    this.organizationUpdate = putEndpoint(
      (organizationId) => `/organizations/${organizationId}`,
    );
    this.queuedSuggestionsCreate = postEndpoint(
      (experimentId) => `/experiments/${experimentId}/queued_suggestions`,
    );
    this.queuedSuggestionsDelete = deleteEndpoint(
      (experimentId, queuedSuggestionId) =>
        `/experiments/${experimentId}/queued_suggestions/${queuedSuggestionId}`,
    );
    this.queuedSuggestionsDetail = getEndpoint(
      (experimentId, queuedSuggestionId) =>
        `/experiments/${experimentId}/queued_suggestions/${queuedSuggestionId}`,
    );
    this.queuedSuggestionsListDetail = getEndpoint(
      (experimentId) => `/experiments/${experimentId}/queued_suggestions`,
    );
    this.resendVerificationEmail = postEndpoint("/verifications");
    this.resetPassword = deleteEndpoint(
      (userId) => `/users/${userId}/sessions`,
    );
    this.sessionDetail = getEndpoint("/sessions");
    this.suggestions = getEndpoint(
      (experimentId) => `/experiments/${experimentId}/suggestions`,
    );
    this.suggestionsCreate = postEndpoint(
      (experimentId) => `/experiments/${experimentId}/suggestions`,
    );
    this.suggestionsDelete = deleteEndpoint(
      (experimentId, suggestionId) =>
        `/experiments/${experimentId}/suggestions/${suggestionId}`,
    );
    this.suggestionsDeleteAll = deleteEndpoint(
      (experimentId) => `/experiments/${experimentId}/suggestions`,
    );
    this.tokenDetailSelf = getEndpoint("/tokens/self");
    this.userDelete = deleteEndpoint((userId) => `/users/${userId}`);
    this.userDetail = getEndpoint((userId) => `/users/${userId}`);
    this.userExperiments = getEndpoint(
      (userId) => `/users/${userId}/experiments`,
    );
    this.userMemberships = getEndpoint(
      (userId) => `/users/${userId}/memberships`,
    );
    this.userPendingPermissions = getEndpoint(
      (userId) => `/users/${userId}/pending_permissions`,
    );
    this.userPermissions = getEndpoint(
      (userId) => `/users/${userId}/permissions`,
    );
    this.userResendVerificationEmail = postEndpoint(
      (userId) => `/users/${userId}/verifications`,
    );
    this.userSession = getEndpoint((userId) => `/users/${userId}/sessions`);
    this.userUpdate = putEndpoint((userId) => `/users/${userId}`);
    /* eslint-enable max-len */
  }

  serializeAs() {
    return this.options;
  }
}

export default LegacyApiClient;
