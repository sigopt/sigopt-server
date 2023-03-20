/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import OrganizationAdminEndpoint from "../server/endpoint";
import {MEMBERSHIP_TYPES} from "../../../constants";
import {pendingPermissionFromPermission} from "../helpers";
import {usersFromMemberships} from "../../../user/helpers";

export default class OrganizationUsersEndpoint extends OrganizationAdminEndpoint {
  pageName() {
    return "Organization Users";
  }
  static page = require("./page");

  ownerOnly = false;

  parseParams(req) {
    return Promise.all([
      this._fetchOrganization(req),
      this._fetchUserMemberships(req),
    ])
      .then(([organization, userMemberships]) => {
        return Promise.all([
          organization,
          userMemberships,
          this._fetchUserAdminClients(organization, req.currentUser),
        ]);
      })
      .then(([organization, userMemberships, clients]) => {
        const isOrgOwner = _.some(
          userMemberships,
          (membership) =>
            membership.organization.id === organization.id &&
            membership.type === MEMBERSHIP_TYPES.OWNER,
        );

        const dataPromise = isOrgOwner
          ? this._fetchOrgOwnerData(organization)
          : this._fetchAdminData(organization, clients);

        return Promise.all([
          clients,
          isOrgOwner,
          dataPromise,
          this._fetchOrganizationToken(req, organization),
        ]);
      })
      .then(
        ([
          clients,
          isOrgOwner,
          {invites, memberships, permissions},
          organizationToken,
        ]) => {
          const appUrl = req.configBroker.get("address.app_url");
          const users = usersFromMemberships(memberships);

          return {
            alertBroker: this.services.alertBroker,
            appUrl,
            canInviteOwners: isOrgOwner,
            clients,
            currentUser: req.currentUser,
            invites,
            isOrgOwner,
            loginState: req.loginState,
            memberships,
            permissions,
            promiseApiClient: this.services.promiseApiClient,
            signupToken: organizationToken,
            users,
          };
        },
      );
  }

  _fetchOrgOwnerData(organization) {
    const invitesReq = this.services.promiseApiClient
      .organizations(organization.id)
      .invites()
      .exhaustivelyPage();
    const membershipReq = this.services.promiseApiClient
      .organizations(organization.id)
      .memberships()
      .exhaustivelyPage();
    const permissionsReq = this.services.promiseApiClient
      .organizations(organization.id)
      .permissions()
      .exhaustivelyPage()
      .then((permissions) => _.filter(permissions, (p) => !p.owner))
      .then((permissions) =>
        _.map(permissions, pendingPermissionFromPermission),
      );
    return Promise.all([invitesReq, membershipReq, permissionsReq]).then(
      ([invites, memberships, permissions]) => ({
        invites,
        memberships,
        permissions,
      }),
    );
  }

  _fetchAdminData(organization, clients) {
    const getClientsResource = (endpoint) =>
      Promise.all(
        _.map(clients, (c) =>
          this.services.promiseApiClient
            .clients(c.id)
            [endpoint]()
            .exhaustivelyPage(),
        ),
      ).then((resources) => _.flatten(resources, true));
    const invitesPromise = getClientsResource("pendingPermissions").then(
      (pendingPermissions) => {
        const groupedByUser = _.chain(pendingPermissions).groupBy(
          (pp) => pp.email,
        );
        return groupedByUser
          .map((pps, email) => ({
            email,
            membership_type: "member",
            object: "invite",
            organization: organization.id,
            organization_name: organization.name,
            pending_permissions: pps,
          }))
          .value();
      },
    );
    const membershipsPromise = getClientsResource("permissions").then(
      (allPermissions) => {
        const allPermissionsAsPending = _.map(
          allPermissions,
          pendingPermissionFromPermission,
        );
        const sampleUserPermissions = _.chain(allPermissions)
          .indexBy((p) => p.user.id)
          .map();
        const memberships = sampleUserPermissions.map((permission) => ({
          object: "membership",
          organization,
          type: permission.is_owner ? "owner" : "member",
          user: permission.user,
        }));
        return {
          memberships: memberships.value(),
          permissions: allPermissionsAsPending,
        };
      },
    );
    return Promise.all([invitesPromise, membershipsPromise]).then(
      ([invites, membershipResults]) => ({
        invites,
        memberships: membershipResults.memberships,
        permissions: membershipResults.permissions,
      }),
    );
  }

  _fetchOrganizationToken(req, organization) {
    const hasSignupLink = organization.allow_signup_from_email_domains;
    if (hasSignupLink && organization.client_for_email_signup) {
      return this.services.promiseApiClient
        .clients(organization.client_for_email_signup)
        .tokens()
        .create();
    } else {
      return Promise.resolve(null);
    }
  }
}
