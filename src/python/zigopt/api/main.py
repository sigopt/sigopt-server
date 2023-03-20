# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import argparse
import logging
import os
import sys

from zigopt.api.prod import ProdApp
from zigopt.brand.constant import PRODUCT_NAME
from zigopt.config.broker import ConfigBroker
from zigopt.log.base import base_logger_setup, configure_loggers
from zigopt.profile.profile import NullProfiler, Profiler
from zigopt.profile.tracer import NullTracer
from zigopt.version import log_version


base_logger_setup()


def _default_app(profiler, tracer):
  config_file = os.environ.get("sigopt_server_config_file")
  config_broker = ConfigBroker.from_file(config_file)
  configure_loggers(config_broker)
  logging.getLogger("sigopt.python").info("Python version: %s", sys.version)
  log_version()
  return ProdApp(profiler, tracer, config_broker)


GUNICORN_ENTRY_POINT = _default_app(NullProfiler(), NullTracer())


def run_app():
  parser = argparse.ArgumentParser(
    description=f"{PRODUCT_NAME} API webapp",
  )

  parser.add_argument(
    "--debug",
    action="store_true",
    default=False,
    help="run app in debug mode",
  )

  parser.add_argument(
    "--profile",
    action="store_true",
    default=False,
    help="run the profiler",
  )

  parser.add_argument(
    "--threaded",
    action="store_true",
    default=False,
    help="run app in threaded mode",
  )

  args = parser.parse_args()

  if args.profile and args.debug:
    raise Exception("The profiler does not work in debug mode")

  profiler = NullProfiler()
  if args.profile:
    profiler = Profiler()

  app = _default_app(profiler, NullTracer())

  try:
    app.debug = args.debug
    app.run(host=app.config_broker["flask.host"], port=app.config_broker["flask.port"], threaded=args.threaded)
  finally:
    profiler.print_stats()


if __name__ == "__main__":
  run_app()
