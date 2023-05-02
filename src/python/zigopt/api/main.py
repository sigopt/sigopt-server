# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import argparse
import logging
import os
import sys

from zigopt.api.prod import ProdApp
from zigopt.brand.constant import PRODUCT_NAME
from zigopt.config import load_config_from_env
from zigopt.contracts import prepare_contracts
from zigopt.log.base import base_logger_setup, configure_loggers
from zigopt.profile.profile import BaseProfiler, NullProfiler, Profiler
from zigopt.profile.tracer import NullTracer
from zigopt.version import log_version


base_logger_setup()


def _default_app(profiler, tracer):
  config_broker = load_config_from_env()
  configure_loggers(config_broker)
  logging.getLogger("sigopt.python").info("Python version: %s", sys.version)
  log_version()
  return ProdApp(profiler, tracer, config_broker)


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

  prepare_contracts()

  profiler: BaseProfiler = NullProfiler()
  if args.profile:
    profiler = Profiler()

  app = _default_app(profiler, NullTracer())

  try:
    app.debug = args.debug
    app.run(
      host=app.config_broker.get("flask.host", "0.0.0.0"),
      port=app.config_broker.get("flask.port", 5000),
      threaded=args.threaded,
    )
  finally:
    profiler.print_stats()


if __name__ == "__main__":
  run_app()
elif os.environ.get("GUNICORN_ENABLED"):
  prepare_contracts()
  GUNICORN_ENTRY_POINT = _default_app(NullProfiler(), NullTracer())
