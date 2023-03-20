#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import logging
import os
import sys

from flasgger import Swagger

from zigopt.api.swaggerapp import SwaggerApp
from zigopt.config.broker import ConfigBroker
from zigopt.log.base import base_logger_setup, configure_loggers
from zigopt.version import log_version


# OpenAPI3 does not support the MERGE verb, this caused it to fail validation. Therefore we are going to loop through
# our paths and remove all MERGE verbs. Especially since the training_run endpoint supports MERGE and PUT with the
# same handler and interface, just different semantics that can be explained in natural language, this is reasonable.
def remove_merge(spec):
  for path in spec["paths"].keys():
    if spec["paths"][path].get("merge", False):
      del spec["paths"][path]["merge"]


# All of this is based on Flasgger code committed since last 0.9.5 release, but never released
def write_documentation(file_to_write, flask_app):
  with flask_app.app_context():
    flask_app.config["SWAGGER"] = {"title": "Sigopt REST API", "openapi": "3.0.2"}
    swagger = Swagger(flask_app)
    endpoint = swagger.config["specs"][0]["endpoint"]
    spec = flask_app.swag.get_apispecs(endpoint)
    remove_merge(spec)
    json.dump(spec, file_to_write, indent=4)


def _default_app():
  config_file = os.environ.get("sigopt_server_config_file")
  config_broker = ConfigBroker.from_file(config_file)
  configure_loggers(config_broker)
  logging.getLogger("sigopt.python").info("Python version: %s", sys.version)
  log_version()
  return SwaggerApp(config_broker)


if __name__ == "__main__":
  base_logger_setup()

  app = _default_app()

  swagger_path = os.environ["SIGOPT_SWAGGER_PATH"]
  swagger_file = os.environ["SIGOPT_SWAGGER_FILENAME"]
  path = os.path.join(swagger_path, swagger_file)
  with open(path, "w") as file:
    logging.getLogger("sigopt.python").info("OpenAPI file open %s", path)
    write_documentation(file, app)
    logging.getLogger("sigopt.python").info("Completed write to file %s", path)
