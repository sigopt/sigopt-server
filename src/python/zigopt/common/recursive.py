# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, Callable, Sequence

import deal

from zigopt.common.maps import filter_keys, map_dict
from zigopt.common.types import is_mapping, is_sequence


__all__ = ["recursively_map_dict", "recursively_filter_keys", "recursively_omit_keys"]


@deal.pre(lambda func, d: isinstance(d, dict))
def recursively_map_dict(func: Callable[[Any], Any], d: dict) -> dict:
  def _inner(func, d):
    if is_mapping(d):
      return map_dict(lambda v: _inner(func, v), d)
    if is_sequence(d):
      return [_inner(func, v) for v in d]
    return func(d)

  return _inner(func, d)


def recursively_filter_keys(func: Callable[[Any], bool], json: Any) -> Any:
  def r_call(item):
    return recursively_filter_keys(func, item)

  if is_sequence(json):
    return [r_call(e) for e in json]

  if is_mapping(json):
    return map_dict(r_call, filter_keys(func, json))

  return json


def recursively_omit_keys(json: Any, keys: Sequence) -> Any:
  return recursively_filter_keys(lambda key: key not in keys, json)
