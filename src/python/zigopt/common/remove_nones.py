# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Hashable, Mapping, Optional, Sequence, TypeVar

import deal


T = TypeVar("T")
GHashable = TypeVar("GHashable", bound=Hashable)

__all__ = ["remove_nones_mapping", "remove_nones_sequence"]


@deal.ensure(lambda dct, result: all(dct[k] is v for k, v in result.items()))
@deal.ensure(lambda dct, result: sum(1 for v in dct.values() if v is not None) == len(result))
@deal.post(lambda result: not any(v is None for v in result.values()))
def remove_nones_mapping(dct: Mapping[GHashable, Optional[T]]) -> dict[GHashable, T]:
  return {k: v for k, v in dct.items() if v is not None}


@deal.ensure(lambda lis, result: all(any(v is e for e in lis) for v in result))
@deal.ensure(lambda lis, result: sum(1 for v in lis if v is not None) == len(result))
@deal.post(lambda result: not any(v is None for v in result))
def remove_nones_sequence(
  lis: Sequence[Optional[T]],
) -> list[T] | tuple[T, ...]:
  return [l for l in lis if l is not None]
