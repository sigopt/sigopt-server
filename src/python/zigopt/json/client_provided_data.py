# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
from typing import Optional

from zigopt.common import *


def client_provided_data_json(
  client_provided_data: Optional[str],
) -> Optional[dict[str, int | float | str]]:
  j: Optional[dict[str, int | float | str]] = napply(client_provided_data, json.loads)
  # NOTE: There shouldn't be any nulls in the data we store in the
  # DB, but we remove them from the JSON here just for safety/consistency
  if j is None:
    return None
  return remove_nones_mapping(j)
