# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.json.builder.experiment import ExperimentJsonBuilder


class AiExperimentJsonBuilder(ExperimentJsonBuilder):
  object_name = "aiexperiment"

  def development(self):
    pass

  def observation_budget(self):
    pass
