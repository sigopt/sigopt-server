/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

// invite.pending_permissions.role
export const InviteRoles = {
  ADMIN: "admin",
  USER: "user",
  READ_ONLY: "read-only",
  NO_ROLE: "uninvited",
};

export const InviteRolesDisplayText = {
  [InviteRoles.ADMIN]: "Admin",
  [InviteRoles.USER]: "Write",
  [InviteRoles.READ_ONLY]: "Read",
};

// Teams
// Exist on permissions object
export const ClientPermissionTypes = {
  // This IS_OWNER refers to the organization - not team.
  IS_OWNER: "is_owner",
  CAN_ADMIN: "can_admin",
  CAN_WRITE: "can_write",
  CAN_READ: "can_read",
};

// Teams
export const ClientPermissionTypesDisplayText = {
  [ClientPermissionTypes.IS_OWNER]: "Owner",
  [ClientPermissionTypes.CAN_ADMIN]: "Admin",
  [ClientPermissionTypes.CAN_WRITE]: "Write",
  [ClientPermissionTypes.CAN_READ]: "Read",
};
