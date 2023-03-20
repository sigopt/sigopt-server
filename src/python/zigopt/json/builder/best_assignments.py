# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.json.builder.observation import ObservationDataJsonBuilder


class BestAssignmentsJsonBuilder(ObservationDataJsonBuilder):
  object_name = "best_assignments"
