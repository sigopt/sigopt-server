#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# -*- coding: utf-8 -*-


import argparse
import logging
import string
from typing import Any

import pg8000
import sqlalchemy
from sigopt_config.broker import ConfigBroker

import zigopt.db.all_models  # pylint: disable=unused-import
from zigopt.common import *
from zigopt.client.model import Client
from zigopt.common.sigopt_datetime import current_datetime, unix_timestamp
from zigopt.db.declarative import Base
from zigopt.db.service import DatabaseConnectionService
from zigopt.experiment.model import Experiment
from zigopt.invite.constant import ADMIN_ROLE, READ_ONLY_ROLE, ROLE_TO_PERMISSION, USER_ROLE
from zigopt.membership.model import Membership, MembershipType
from zigopt.note.model import ProjectNote
from zigopt.organization.model import Organization
from zigopt.permission.model import Permission
from zigopt.protobuf.dict import dict_to_protobuf_struct
from zigopt.protobuf.gen.client.clientmeta_pb2 import ClientMeta
from zigopt.protobuf.gen.experiment.experimentmeta_pb2 import (
  PARAMETER_DOUBLE,
  PARAMETER_INT,
  ExperimentMeta,
  ExperimentParameter,
)
from zigopt.protobuf.gen.organization.organizationmeta_pb2 import OrganizationMeta
from zigopt.protobuf.gen.permission.permissionmeta_pb2 import PermissionMeta
from zigopt.protobuf.gen.token.tokenmeta_pb2 import WRITE, TokenMeta
from zigopt.protobuf.gen.training_run.training_run_data_pb2 import (
  Dataset,
  Log,
  SourceCode,
  TrainingRunData,
  TrainingRunModel,
  TrainingRunValue,
)
from zigopt.protobuf.gen.user.usermeta_pb2 import UserMeta
from zigopt.redis.service import RedisServiceError
from zigopt.services.api import ApiRequestLocalServiceBag, ApiServiceBag
from zigopt.token.model import Token
from zigopt.token.token_types import TokenType
from zigopt.training_run.model import TrainingRun
from zigopt.user.model import User, password_hash
from zigopt.utils.create_produser import execute_query, make_produser


DB_NAME_ALLOW_LIST = ["testdb", "basedb"]
USERNAME_ALLOW_LIST = ["testuser", "sigoptrds", "produser"]

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("sigopt.rawsql").setLevel(logging.WARNING)
logging.getLogger("sigopt.sql").setLevel(logging.WARNING)


def create_user(services, user_def):
  user_meta = UserMeta()
  user_meta.date_created = unix_timestamp()
  user_meta.has_verified_email = bool(user_def.get("has_verified_email"))
  plaintext_password = user_def.get("password", None)
  hashed_password = (
    password_hash(plaintext_password, work_factor=services.config_broker.get("user.password_work_factor"))
    if plaintext_password
    else None
  )
  user = User(
    name=user_def.get("name", "Anonymous"),
    email=user_def["email"],
    hashed_password=hashed_password,
    user_meta=user_meta,
  )
  services.database_service.insert(user)
  return user


def setup_db(config_broker, allow_list=True, superuser=None, superuser_password=None):
  database = config_broker.get("db.path")
  # NOTE: Use allow_list to check for unsafe names instead of using query_args because
  # pg8000's execute only works for quoted arguments - db names and roles are
  # not quoted in sql queries.
  if allow_list:
    assert database in DB_NAME_ALLOW_LIST

  # Connect as default superuser
  args: dict[str, Any] = {
    "user": superuser or "postgres",
    "password": superuser_password,
    "host": config_broker.get("db.host"),
    "port": config_broker.get("db.port"),
    **(config_broker.get("db.query") or {}),
  }
  conn = pg8000.connect(**remove_nones(args))
  try:
    conn.autocommit = True
    with conn.cursor() as cursor:
      logging.info("Creating database %s", database)
      created_db = execute_query(
        conn=conn,
        cursor=cursor,
        query_string=f"CREATE DATABASE {database}",
        error_allow_list=[
          dict(
            error_str="already exists",
            warning='database: "' + database + '" already exists. Existing database will be used.',
          )
        ],
      )
  finally:
    conn.close()
  return created_db


def create_owner(services, user_id, organization_id, client_ids):
  services.database_service.insert(
    Membership(
      user_id=user_id,
      organization_id=organization_id,
      membership_type=MembershipType.owner,
    )
  )


def create_permission(services, user_id, client_id, permission_meta):
  organization_id = services.database_service.one(
    services.database_service.query(Client).filter(Client.id == client_id)
  ).organization_id
  try:
    services.database_service.insert(
      Membership(
        user_id=user_id,
        organization_id=organization_id,
        membership_type=MembershipType.member,
      )
    )
  except sqlalchemy.exc.IntegrityError:
    services.database_service.rollback_session()
  services.database_service.insert(
    Permission(
      user_id=user_id,
      client_id=client_id,
      organization_id=organization_id,
      permission_meta=permission_meta,
    )
  )


def make_user_in_client(services, client, name, email, role_type):
  user_meta = UserMeta()
  user_meta.has_verified_email = True
  user_meta.date_created = unix_timestamp()
  user = User(
    name=name,
    email=email,
    plaintext_password="password",
    user_meta=user_meta,
  )
  services.database_service.insert(user)

  if client:
    permission_meta = PermissionMeta()
    permission_meta.can_admin = role_type.can_admin
    permission_meta.can_write = role_type.can_write
    permission_meta.can_read = role_type.can_read
    create_permission(services=services, user_id=user.id, client_id=client.id, permission_meta=permission_meta)
    meta = TokenMeta()
    meta.date_created = unix_timestamp()
    services.database_service.insert(
      Token(
        token_type=TokenType.USER,
        client_id=None,
        user_id=user.id,
        meta=meta,
        token="".join(c for c in name if c in string.printable) + "user_token",
      )
    )
  return user


def create_organization(services, **kwargs):
  organization = Organization(**kwargs)
  services.database_service.insert(organization)
  return organization


def create_client(services, name, **kwargs):
  organization_meta = OrganizationMeta()
  organization = create_organization(services, name=name, organization_meta=organization_meta)
  client = Client(organization_id=organization.id, name=name, **kwargs)
  services.database_service.insert(client)
  project = services.project_service.create_example_for_client(client_id=client.id)
  return client, project


def purge_redis_database(services):
  logging.info("purging redis database")
  try:
    services.redis_service.dangerously_purge_database()
  except RedisServiceError:
    logging.warning("failed to purge redis database - maybe one isn't running")


def get_root_engine(config_broker, superuser=None, superuser_password=None, echo=False):
  return DatabaseConnectionService.make_engine(
    config_broker.get("db"),
    user=superuser or "postgres",
    password=superuser_password,
    echo=echo,
  )


def create_db(
  config_dir,
  config_broker,
  fake_data,
  drop_tables,
  superuser=None,
  superuser_password=None,
  allow_list=True,
  initialize_data=True,
  echo=False,
):
  # pylint: disable=too-many-locals,too-many-statements
  root_engine = get_root_engine(
    config_broker,
    superuser=superuser,
    superuser_password=superuser_password,
    echo=echo,
  )

  if drop_tables:
    Base.metadata.drop_all(root_engine)
  Base.metadata.create_all(root_engine)

  logging.info("All tables:")
  for t in Base.metadata.sorted_tables:
    logging.info(t.name)

  # NOTE: Use allow_list to check for unsafe names instead of using query_args because
  # pg8000's execute only works for quoted arguments - db names and roles are
  # not quoted in sql queries.
  host = config_broker.get("db.host")
  port = config_broker.get("db.port")
  database = config_broker.get("db.path")
  username = config_broker.get("db.user")
  password = config_broker.get("db.password")
  query = config_broker.get("db.query")
  if allow_list:
    assert username in USERNAME_ALLOW_LIST
  make_produser(
    host=host,
    port=port,
    database=database,
    query=query,
    produser=username,
    produser_password=password,
    superuser=superuser,
    superuser_password=superuser_password,
  )

  global_services = ApiServiceBag(config_broker, is_qworker=False)
  services = ApiRequestLocalServiceBag(global_services)

  services.database_service.start_session()

  if initialize_data:
    if config_broker.get("clients.client"):
      client_name = config_broker["clients.client.name"]
      client_id = config_broker["clients.client.id"]
      client_meta = ClientMeta()
      client_meta.date_created = unix_timestamp()
      client, project = create_client(services, id=client_id, name=client_name, client_meta=client_meta)
      root_engine.execute(f"GRANT UPDATE ON SEQUENCE clients_id_seq TO {username}")
      services.database_service.execute(
        sqlalchemy.text("SELECT setval(:sequence_name, :client_id)"),
        sequence_name="clients_id_seq",
        client_id=client_id + 1,
      ).fetchall()
      root_engine.execute(f"REVOKE UPDATE ON SEQUENCE clients_id_seq FROM {username}")

      for sibling_name in config_broker.get("clients.siblings", []):
        sibling_client = services.client_service.insert(
          Client(organization_id=client.organization_id, name=sibling_name)
        )
        services.project_service.create_example_for_client(client_id=sibling_client.id)

      if config_broker.get("clients.client.user"):
        user = create_user(services, config_broker.get("clients.client.user"))
        create_owner(
          services=services,
          user_id=user.id,
          organization_id=client.organization_id,
          client_ids=[client.id],
        )
    else:
      client = None

  if fake_data:
    for name, email, role in [
      ("user 👑 sigopt", "user@sigopt.ninja", ROLE_TO_PERMISSION[ADMIN_ROLE]),
      ("admin 2", "admin2@sigopt.ninja", ROLE_TO_PERMISSION[ADMIN_ROLE]),
      ("write user", "write@sigopt.ninja", ROLE_TO_PERMISSION[USER_ROLE]),
      ("read only", "read@sigopt.ninja", ROLE_TO_PERMISSION[READ_ONLY_ROLE]),
      ("maybe user 👑 sigopt", "maybe@sigopt.ninja", ROLE_TO_PERMISSION[USER_ROLE]),
      ("possibly user", "poss@sigopt.ninja", ROLE_TO_PERMISSION[USER_ROLE]),
      ("emojiless user", "noemoji@sigopt.ninja", ROLE_TO_PERMISSION[READ_ONLY_ROLE]),
    ]:
      make_user_in_client(services, client, name, email, role)
    if client:
      param1 = ExperimentParameter()
      param1.name = "param 👽 1"
      param1.bounds.minimum = 0.0
      param1.bounds.maximum = 4.0
      param1.param_type = PARAMETER_DOUBLE

      param2 = ExperimentParameter()
      param2.name = "param 😾 2"
      param2.bounds.minimum = 0.0
      param2.bounds.maximum = 4.0
      param2.param_type = PARAMETER_INT

      experiment_meta_1 = ExperimentMeta()
      experiment_meta_1.all_parameters_unsorted.extend([param1, param2])
      experiment_meta_1.experiment_type = ExperimentMeta.OFFLINE

      services.database_service.insert(
        Experiment(
          name="SigOpt Test 👬  Experiment",
          client_id=client.id,
          date_created=current_datetime(),
          date_updated=current_datetime(),
          created_by=1,
          experiment_meta=experiment_meta_1,
        ),
      )
      meta = TokenMeta()
      meta.date_created = unix_timestamp()
      meta.guest_permissions = WRITE
      services.database_service.insert(
        Token(token_type=TokenType.GUEST, client_id=client.id, user_id=None, meta=meta, token="client_token")
      )

      services.training_run_service.insert_training_runs(
        [
          TrainingRun(
            client_id=client.id,
            project_id=project.id,
            created_by=1,
            training_run_data=TrainingRunData(
              metadata=dict_to_protobuf_struct({"metadata_string": "abc", "metadata_double": 1.0}),
              assignments_struct=dict_to_protobuf_struct({"learning_rate": 0.1, "categorical": "abc"}),
              values_map={"accuracy": TrainingRunValue(value=0.99, value_var=0.01)},
              state=TrainingRunData.COMPLETED,
              name="My first Run",
              datasets={
                "iris": Dataset(),
              },
              source_code=SourceCode(
                content=None,
                hash="abcdef",
              ),
              logs={
                "stdout": Log(
                  content="This is not real code\n",
                ),
              },
              training_run_model=TrainingRunModel(
                type="xgboost",
              ),
            ),
          )
        ]
      )

      services.note_service.insert(
        ProjectNote(
          contents="Example note left on a project",
          created_by=1,
          project_client_id=client.id,
          project_project_id=project.id,
        )
      )
      services.note_service.insert(
        ProjectNote(
          contents="Example note left on a project. But this time, updated!",
          created_by=1,
          project_client_id=client.id,
          project_project_id=project.id,
        )
      )

    # Add a non-sigopt client & user for testing
    owner_user_meta = UserMeta()
    owner_user_meta.has_verified_email = True
    owner_user_meta.date_created = unix_timestamp()
    owner_user = User(
      name="notsigopt",
      email="notsigopt@notsigopt.ninja",
      plaintext_password="password",
      user_meta=owner_user_meta,
    )
    services.database_service.insert(owner_user)

    member_user_meta = UserMeta()
    member_user_meta.has_verified_email = True
    member_user_meta.date_created = unix_timestamp()
    member_user = User(
      name="notsigopt member",
      email="notsigopt_member@notsigopt.ninja",
      plaintext_password="password",
      user_meta=member_user_meta,
    )
    services.database_service.insert(member_user)

    client_name = "Not 🔫 SigOpt"
    client_meta = ClientMeta()
    client_meta.date_created = unix_timestamp()
    client.client_meta = client_meta
    client, project = create_client(
      services,
      name=client_name,
      client_meta=client_meta,
    )

    create_owner(
      services=services,
      user_id=owner_user.id,
      organization_id=client.organization_id,
      client_ids=[client.id],
    )

    permission_meta = PermissionMeta()
    permission_meta.can_admin = True
    permission_meta.can_write = True
    permission_meta.can_read = True
    create_permission(services=services, user_id=member_user.id, client_id=client.id, permission_meta=permission_meta)

    meta = TokenMeta()
    meta.date_created = unix_timestamp()
    services.database_service.insert(
      Token(token_type=TokenType.USER, client_id=None, user_id=owner_user.id, meta=meta, token="fake_user_token")
    )
    meta.guest_permissions = WRITE
    services.database_service.insert(
      Token(token_type=TokenType.GUEST, client_id=client.id, user_id=None, meta=meta, token="fake_client_token")
    )

  services.database_service.end_session()
  purge_redis_database(services)


def parse_args():
  parser = argparse.ArgumentParser(
    description="Create API db",
  )

  parser.add_argument(
    "config_dir",
    type=str,
    help="config directory for db",
  )

  parser.add_argument(
    "--fake-data",
    action="store_true",
    default=False,
    help="init db with fake data",
  )

  parser.add_argument(
    "--drop-tables",
    action="store_true",
    default=False,
    help="drop all tables (before filling fake data)",
  )

  parser.add_argument(
    "--initialize-data",
    dest="initialize_data",
    action="store_true",
    help="create initial orgs, clients and users",
  )
  parser.add_argument(
    "--no-initialize-data",
    dest="initialize_data",
    action="store_false",
    help="dont create initial orgs, clients and users",
  )
  parser.set_defaults(initialize_data=True)

  return parser.parse_args()


def main():
  the_args = parse_args()

  config_dir = the_args.config_dir

  config_broker = ConfigBroker.from_directory(config_dir)
  config_broker.data.setdefault("redis", {})["enabled"] = False
  config_broker.data.setdefault("user_uploads", {}).setdefault("s3", {})["enabled"] = False
  should_populate = setup_db(config_broker=config_broker)

  # Won't try to populate db unless explicitly told or a new db was created
  if should_populate or the_args.fake_data or the_args.drop_tables:
    logging.info("Populating db")
    create_db(
      config_dir=the_args.config_dir,
      config_broker=config_broker,
      fake_data=the_args.fake_data,
      drop_tables=the_args.drop_tables,
      initialize_data=the_args.initialize_data,
      echo=True,
    )


if __name__ == "__main__":
  main()
