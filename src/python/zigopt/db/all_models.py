# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# Makes sure that all model classes are imported, so that they can be registered
# by `declarative_base` and be visible to SQLAlchemy

# pylint: disable=unused-import

import zigopt.checkpoint.model
import zigopt.client.model
import zigopt.experiment.model
import zigopt.file.model
import zigopt.invite.model
import zigopt.membership.model
import zigopt.note.model
import zigopt.observation.model
import zigopt.optimization_aux.model
import zigopt.organization.model
import zigopt.permission.model
import zigopt.permission.pending.model
import zigopt.project.model
import zigopt.queued_suggestion.model
import zigopt.suggestion.processed.model
import zigopt.suggestion.unprocessed.model
import zigopt.tag.model
import zigopt.token.model
import zigopt.training_run.model
import zigopt.user.model
import zigopt.web_data.model
