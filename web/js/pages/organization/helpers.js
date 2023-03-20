/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {getInviteRoleFromPermission} from "../../user/helpers";

export const pendingPermissionFromPermission = (permission) => ({
  client: permission.client.id,
  client_name: permission.client.name,
  email: permission.user.email,
  role: getInviteRoleFromPermission(permission),
});
