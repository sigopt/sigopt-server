# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any as _Any
from typing import Sequence as _Sequence

from zigopt.common.lists import is_mapping


def recursively_check_for_instances(obj: _Any, check: type | _Sequence[type], ignore: type | _Sequence[type] = ()):
  def recursively_check_for_instances_helper(obj, check, ignore, seen):
    str_id = str(id(obj))
    if seen.get(str_id, False):
      return False
    seen[str(id(obj))] = True

    if isinstance(obj, check):
      return True

    if isinstance(obj, ignore):
      return False

    if hasattr(obj, "__dict__"):
      for _, v in list(vars(obj).items()):
        if recursively_check_for_instances_helper(v, check, ignore, seen):
          return True
    elif is_mapping(obj):
      for _, v in list(obj.items()):
        if recursively_check_for_instances_helper(v, check, ignore, seen):
          return True

    return False

  return recursively_check_for_instances_helper(obj, check, ignore, {})
