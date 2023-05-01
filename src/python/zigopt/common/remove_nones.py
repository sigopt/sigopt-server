# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# crosshair: on
from typing import Hashable, Mapping, Optional, Sequence, TypeVar

import deal


lists_T = TypeVar("lists_T")
lists_GHashable = TypeVar("lists_GHashable", bound=Hashable)

__all__ = ["remove_nones_mapping", "remove_nones_sequence"]


@deal.ensure(lambda dct, result: all(dct[k] is v for k, v in result.items()))
@deal.ensure(lambda dct, result: sum(1 for v in dct.values() if v is not None) == len(result))
@deal.post(lambda result: not any(v is None for v in result.values()))
def remove_nones_mapping(dct: Mapping[lists_GHashable, Optional[lists_T]]) -> dict[lists_GHashable, lists_T]:
  return {k: v for k, v in dct.items() if v is not None}


@deal.ensure(lambda lis, result: all(v in lis for v in result))
@deal.ensure(lambda lis, result: sum(1 for v in lis if v is not None) == len(result))
@deal.post(lambda result: not any(v is None for v in result))
def remove_nones_sequence(
  lis: Sequence[Optional[lists_T]],
) -> list[lists_T] | tuple[lists_T, ...]:
  return [l for l in lis if l is not None]
