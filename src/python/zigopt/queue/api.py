# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0

import argparse
import logging
import os
import sys

from zigopt.config.broker import ConfigBroker
from zigopt.log.base import base_logger_setup, configure_loggers
from zigopt.profile.profile import NullProfiler, Profiler
from zigopt.queue.exceptions import WorkerInterruptedException
from zigopt.queue.message_groups import MessageGroup
from zigopt.queue.workers import QueueWorkers, SignalKillPolicy
from zigopt.services.api import ApiRequestLocalServiceBag, ApiServiceBag
from zigopt.version import log_version


parser = argparse.ArgumentParser(
  description="Queue Workers",
)
MESSAGE_GROUPS = list(MessageGroup)
parser.add_argument("message_group", type=MessageGroup, choices=MESSAGE_GROUPS, help="The message group to process.")
parser.add_argument("--profile", action="store_true")
parser.add_argument("--graceful-exit-code", type=int, default=0)
parser.add_argument("--interrupted-exit-code", type=int, default=0)

if __name__ == "__main__":
  base_logger_setup()
  args = parser.parse_args()
  config_file = os.environ["sigopt_server_config_file"]
  config_broker = ConfigBroker.from_file(config_file)
  configure_loggers(config_broker)
  config_broker.log_configs()

  profiler = NullProfiler()
  if args.profile:
    profiler = Profiler()

  logging.getLogger("sigopt.python").info("Python version: %s", sys.version)
  log_version()
  global_services = ApiServiceBag(config_broker, is_qworker=True)
  request_local_services_factory = ApiRequestLocalServiceBag

  workers = QueueWorkers(
    args.message_group,
    global_services,
    kill_policy=SignalKillPolicy(),
    profiler=profiler,
    request_local_services_factory=request_local_services_factory,
  )
  if os.environ.get("QWORKER_HEALTH_CHECK", False):
    global_services.logging_service.getLogger("sigopt.queue.workers.messages").info(
      "Running test for the worker processing %s messages", args.message_group.value
    )
    workers.test()
  else:
    try:
      workers.run()
    except WorkerInterruptedException:
      sys.exit(args.interrupted_exit_code)
    sys.exit(args.graceful_exit_code)
