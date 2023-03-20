# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.handlers.aiexperiments.base import AiExperimentHandler
from zigopt.handlers.experiments.best_training_runs import ExperimentsBestTrainingRunsHandler


class AiExperimentsBestTrainingRunsHandler(ExperimentsBestTrainingRunsHandler, AiExperimentHandler):
  pass
