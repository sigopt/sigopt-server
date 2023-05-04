# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Hashable, Mapping, Optional, Sequence, TypeVar

import deal


T = TypeVar("T")
GHashable = TypeVar("GHashable", bound=Hashable)

__all__ = ["compact_mapping", "compact_sequence"]


@deal.ensure(lambda dct, result: all(dct[k] is v for k, v in result.items()))
@deal.ensure(lambda dct, result: sum(1 for v in dct.values() if v) == len(result))
@deal.post(lambda result: all(result.values()))
def compact_mapping(dct: Mapping[GHashable, Optional[T]]) -> dict[GHashable, T]:
  return {k: v for k, v in dct.items() if v}


@deal.ensure(lambda lis, result: all(v in lis for v in result))
@deal.ensure(lambda lis, result: sum(1 for v in lis if v) == len(result))
@deal.post(all)
def compact_sequence(lis: Sequence[Optional[T]]) -> list[T]:
  return [l for l in lis if l]
