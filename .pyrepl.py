# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# pylint: disable=global-statement
import argparse
from typing import Any

from sigopt_config.broker import ConfigBroker

from zigopt.common import *
from zigopt.db.service import DatabaseConnection, DatabaseService
from zigopt.services.api import ApiRequestLocalServiceBag, ApiServiceBag


config_broker, global_services, services, conn = (None, None, None, None)


def make_cleanup_db_service(_services):
  db_config = _services.config_broker.get_object("db")
  return DatabaseService(
    _services,
    DatabaseConnection(
      _services.database_connection_service.make_engine(
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
    "--config-dir",
    "-c",
    type=str,
    default="/etc/sigopt/server-config/",
    help="Config directory",
  )
  parser.add_argument(
    "--cleanup",
    "-C",
    action="store_true",
    help="Use the cleanup role to connect to the database. Use this role when running backfills.",
  )

  args = parser.parse_args()

  global config_broker
  ServiceBag = ApiServiceBag
  RequestLocalServiceBag = ApiRequestLocalServiceBag
  kwargs: dict[str, Any] = {}
  config_broker = ConfigBroker.from_directory(args.config_dir)
  global global_services
  global_services = ServiceBag.from_config_broker(config_broker, **kwargs)
  global services
  services = RequestLocalServiceBag(global_services)

  if args.cleanup:
    db_config = dict(services.config_broker["db"])
    if not db_config.get("cleanup_user") or not db_config.get("cleanup_password"):
      raise Exception("You must specify cleanup_user and cleanup_password in the db section of your config.")
    services.database_service = make_cleanup_db_service(services)

  services.database_service.start_session()


if __name__ == "__main__":
  main()
