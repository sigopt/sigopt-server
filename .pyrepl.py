# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import argparse
import os
import warnings

from zigopt.common import *
from zigopt.config.broker import ConfigBroker
from zigopt.db.service import DatabaseConnection, DatabaseService
from zigopt.services.api import ApiRequestLocalServiceBag, ApiServiceBag


config_broker, global_services, services, conn = (None, None, None, None)


def make_cleanup_db_service(services):
  db_config = services.config_broker.get_object("db")
  return DatabaseService(
    services,
    DatabaseConnection(
      services.database_connection_service.make_engine(
        db_config,
        user=db_config.get("cleanup_user"),
        password=db_config.get("cleanup_password"),
      ),
    ),
  )


def main():
  parser = argparse.ArgumentParser()
  repl_flags = parser.add_mutually_exclusive_group()
  repl_flags.add_argument(
    "--config",
    "-c",
    type=str,
    default="config/development.json",
    help=(
      'Config file name, joined by "," if multiple.'
      " If multiple config files contain the same values,"
      " files specified earlier will take precedence."
    ),
  )
  parser.add_argument(
    "--cleanup",
    "-C",
    action="store_true",
    help="Use the cleanup role to connect to the database. Use this role when running backfills.",
  )

  args = parser.parse_args()

  if args.config:
    config = args.config
  else:
    config = "config/development.json"

  if config == "config/development.json" and not os.environ.get("SIGOPT_CONTAINER_ENV"):
    warnings.warn(
      (
        "Attempting to start repl outside of the repl container."
        " Please run ./scripts/launch/repl locally, or choose the correct environment."
      ),
      RuntimeWarning,
    )
    response = input("Continue with development repl (Y/n)? ")
    if not response.lower().startswith("y"):
      return

  global config_broker
  ServiceBag = ApiServiceBag
  RequestLocalServiceBag = ApiRequestLocalServiceBag
  kwargs = {}
  config_broker = ConfigBroker.from_file(config)
  global global_services
  global_services = ServiceBag.from_config_broker(config_broker, **kwargs)
  global services
  services = RequestLocalServiceBag(global_services)

  if args.cleanup:
    db_config = services.config_broker.get_object("db")
    if not db_config.get("cleanup_user") or not db_config.get("cleanup_password"):
      raise Exception("You must specify cleanup_user and cleanup_password in the db section of your config file.")
    services.database_service = make_cleanup_db_service(services)

  services.database_service.start_session()


if __name__ == "__main__":
  main()
