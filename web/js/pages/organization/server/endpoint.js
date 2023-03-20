/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import LoggedInReactEndpoint from "../../../server/endpoint/loggedin";
import {NotFoundError} from "../../../net/errors";

const rejectNotFound = (req) =>
  Promise.reject(new NotFoundError({path: req.path}));

export default class OrganizationAdminEndpoint extends LoggedInReactEndpoint {
  ownerOnly = true;

  getParams(req) {
    if (!req.loginState.userId) {
      return rejectNotFound(req);
    }
    return Promise.all([
      this._fetchOrganization(req),
      this._fetchUserPermissions(req),
      this._fetchUserMemberships(req),
    ])
      .then(([organization, userPermissions, userMemberships]) => {
        const currentMembership = _.find(
          userMemberships,
          (m) => m.organization.id === organization.id,
        );
        const currentPermissions = _.filter(
          userPermissions,
          (p) => p.client.organization === organization.id,
        );

        const isMember = currentMembership;
        const isOwner = currentMembership && currentMembership.type === "owner";
        const isAdmin =
          isMember && _.any(currentPermissions, (c) => c.can_admin);

        const canSeePage = isOwner || (isAdmin && !this.ownerOnly);
        // TODO(SN-1169): Only used to toggle hiding in the sidebar, would be cooler if we could
        // just dynamically hide endpoints from the sidebar that are `ownerOnly = true`
        const canSeeExperimentsPage = isOwner;

        if (canSeePage) {
          return {
            alertBroker: req.services.alertBroker,
            canSeeExperimentsPage: Boolean(canSeeExperimentsPage),
            legacyApiClient: req.services.legacyApiClient,
            loginState: req.loginState,
            navigator: this.services.navigator,
            organization: organization,
            path: req.path,
            promiseApiClient: req.services.promiseApiClient,
          };
        }

        return rejectNotFound(req);
      })
      .then((params) =>
        super
          .getParams(req)
          .then((superParams) => _.extend(superParams, params)),
      );
  }

  _fetchOrganization(req) {
    if (req.matchedOrganization) {
      return Promise.resolve(req.matchedOrganization);
    } else if (req.loginState.clientId) {
      return this.services.promiseApiClient
        .clients(req.loginState.clientId)
        .fetch()
        .then(([client]) => {
          if (client) {
            return Promise.resolve(client.organization);
          } else {
            return rejectNotFound(req);
          }
        })
        .then((organizationId) => this._fetchOrganizationById(organizationId));
    } else {
      return rejectNotFound(req);
    }
  }

  _fetchOrganizationById(organizationId) {
    if (organizationId) {
      return this.services.promiseApiClient
        .organizations(organizationId)
        .fetch();
    } else {
      return Promise.resolve(null);
    }
  }

  _fetchUserPermissions(req) {
    return this.services.promiseApiClient
      .users(req.loginState.userId)
      .permissions()
      .exhaustivelyPage();
  }

  _fetchUserMemberships(req) {
    return this.services.promiseApiClient
      .users(req.loginState.userId)
      .memberships()
      .exhaustivelyPage();
  }

  _fetchUserAdminClients(organization, currentUser) {
    return this.services.promiseApiClient
      .organizations(organization.id)
      .clients()
      .exhaustivelyPage()
      .catch((err) => {
        if (_.contains([403, 403], err.status)) {
          return this.services.promiseApiClient
            .users(currentUser.id)
            .permissions()
            .exhaustivelyPage({organization: organization.id})
            .then((memberships) =>
              _.chain(memberships).filter("can_admin").pluck("client").value(),
            );
        } else {
          return Promise.reject(err);
        }
      });
  }
}
