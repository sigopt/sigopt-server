#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os
import sys

from vulture.config import DEFAULTS, make_config
from vulture.core import Vulture


DEFAULTS.update(
  {
    "exclude": [
      "node_modules/",
      "scratch/",
      "src/python/zigopt/db/all_models.py",
      "venv/",
      "web/fonts/",
    ],
    "ignore_decorators": [
      # databse
      "@compiles",
      # flask
      "@*.errorhandler",
      # json builder
      "@expose_fields",
      "@field",
      # tests
      "@pytest.*",
    ],
    "ignore_names": [
      "zigopt",
      # database
      "autocommit",
      "autoflush",
      # flask
      "make_default_options_response",
      "request_class",
      "want_form_data_parsed",
      # gunicorn
      "GUNICORN_ENTRY_POINT",
      # logging
      "converter",
      "exc_text",
      "formatMessage",
      "funcName",
      "levelno",
      "lineno",
      "longrepr",
      "msecs",
      "pathname",
      "query_time",
      # smtp
      "content_manager",
      "handle_DATA",
      "mail_settings",
      # sqlalchemy
      "impl",
      "process_*_param",
      # tests
      "pytest_*",
      "side_effect",
      "test_*",
      # types
      "type_*",
      # protobuf
      "_options",
      "_serialized_*",
      "containing_*",
      "google_dot_protobuf_dot_*",
      "zigopt_dot_protobuf_dot_gen_dot_*",
    ],
    "paths": ["."],
  }
)

allowlist_path = ".vulture_allowlist"

if __name__ == "__main__":
  config = make_config()
  vulture = Vulture(
    verbose=config["verbose"],
    ignore_names=config["ignore_names"],
    ignore_decorators=config["ignore_decorators"],
  )
  min_confidence = config["min_confidence"]
  sort_by_size = config["sort_by_size"]
  allow_list = config["make_whitelist"]
  paths = config["paths"]
  if not allow_list:
    paths.append(allowlist_path)
  vulture.scavenge(paths, exclude=config["exclude"])
  found_dead_code_or_error = False
  pwd = os.getcwd()
  with open(allowlist_path, "w+", encoding="utf-8") if allow_list else sys.stdout as fp:
    for item in vulture.get_unused_code(min_confidence=min_confidence, sort_by_size=sort_by_size):
      print(  # noqa: T001
        item.get_whitelist_string().rstrip().replace(pwd + "/", "")
        if allow_list
        else item.get_report(add_size=sort_by_size),
        file=fp,
      )
      found_dead_code_or_error = True
  if not allow_list:
    sys.exit(found_dead_code_or_error)
