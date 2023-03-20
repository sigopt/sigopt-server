# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging
import os

from zigopt.git.status import get_git_hash


def log_version():
  logger = logging.getLogger("sigopt.version")
  env_key = "sigopt_server_version"
  version = "unknown"
  try:
    version = os.environ[env_key]
  except KeyError:
    try:
      git_hash = get_git_hash(os.path.dirname(__file__))
      version = f"git:{git_hash}"
    except AssertionError:
      raise
    except Exception:
      logger.exception("unknown git-hash")
  logger.info(version)
