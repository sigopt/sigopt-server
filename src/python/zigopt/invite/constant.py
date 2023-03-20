# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.net.errors import ConflictingDataError
from zigopt.protobuf.gen.permission.permissionmeta_pb2 import PermissionMeta


"""Constants for ``sigopt-server`` invite-role components."""
ADMIN_ROLE = "admin"
USER_ROLE = "user"
READ_ONLY_ROLE = "read-only"
NO_ROLE = "uninvited"

ALL_ROLES = [ADMIN_ROLE, USER_ROLE, READ_ONLY_ROLE, NO_ROLE]

ROLE_TO_PERMISSION = {
  ADMIN_ROLE: PermissionMeta(can_read=True, can_write=True, can_admin=True),
  USER_ROLE: PermissionMeta(can_read=True, can_write=True, can_admin=False),
  READ_ONLY_ROLE: PermissionMeta(can_read=True, can_write=False, can_admin=False),
  NO_ROLE: PermissionMeta(can_read=False, can_write=False, can_admin=False),
}


def permission_to_role(permission):
  if not permission:
    return NO_ROLE

  if permission.can_read and permission.can_write and permission.can_admin:
    return ADMIN_ROLE
  elif permission.can_read and permission.can_write and not permission.can_admin:
    return USER_ROLE
  elif permission.can_read and not permission.can_write and not permission.can_admin:
    return READ_ONLY_ROLE
  elif not permission.can_read and not permission.can_write and not permission.can_admin:
    return NO_ROLE

  raise ConflictingDataError(f"This permission set is not supported: {permission}")
