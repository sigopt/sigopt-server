/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {
  ClientPermissionTypes,
  ClientPermissionTypesDisplayText,
  InviteRoles,
  InviteRolesDisplayText,
} from "./roles";

export const clientPermissionsDisplayText = function (permission) {
  if (permission[ClientPermissionTypes.IS_OWNER]) {
    return ClientPermissionTypesDisplayText[ClientPermissionTypes.IS_OWNER];
  } else if (permission[ClientPermissionTypes.CAN_ADMIN]) {
    return ClientPermissionTypesDisplayText[ClientPermissionTypes.CAN_ADMIN];
  } else if (permission[ClientPermissionTypes.CAN_WRITE]) {
    return ClientPermissionTypesDisplayText[ClientPermissionTypes.CAN_WRITE];
  } else if (permission[ClientPermissionTypes.CAN_READ]) {
    return ClientPermissionTypesDisplayText[ClientPermissionTypes.CAN_READ];
  }
  throw new Error(`Unexpected permission type in state ${permission}`);
};

export const getInviteRoleFromPermission = function (permission) {
  if (permission.can_admin && permission.can_write && permission.can_read) {
    return InviteRoles.ADMIN;
  } else if (permission.can_write && permission.can_read) {
    return InviteRoles.USER;
  } else if (permission.can_read) {
    return InviteRoles.READ_ONLY;
  }
  return InviteRoles.NO_ROLE;
};

export const getInviteRoleDisplayText = function (role) {
  const roleText = InviteRolesDisplayText[role];
  if (roleText) {
    return roleText;
  } else {
    throw new Error(`Unexpected invite type in state ${role}`);
  }
};

const userFromMembership = (membership) =>
  _.extend({}, membership.user, {
    organizationRole: membership.type,
    organization: membership.organization,
  });
export const usersFromMemberships = (memberships) =>
  _.map(memberships, userFromMembership);
const userPermissionsFromAllPermisions = (user, permissions) =>
  _.filter(permissions, (permission) => permission.user.id === user.id);

const userClientsFromUsersPermissions = (permissions) => {
  return _.map(permissions, (permission) => {
    const client = _.clone(permission.client);
    const onlyPermissions = _.omit(permission, "user", "client");
    return _.extend(client, {userPermissions: onlyPermissions});
  });
};

export const usersWithClients = (memberships, permissions) => {
  const users = usersFromMemberships(memberships);
  return _.map(users, (user) => {
    const userPermissions = userPermissionsFromAllPermisions(user, permissions);
    const userClients = userClientsFromUsersPermissions(userPermissions);
    return _.extend({}, user, {clients: userClients});
  });
};
