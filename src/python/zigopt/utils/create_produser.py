#!/usr/bin/env python3
# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging
from contextlib import contextmanager
from typing import Any

import pg8000

from zigopt.common import *


DELETE_ALLOW_LIST = ["tokens", "invites", "roles", "experiment_optimization_aux", "memberships", "pending_permissions"]


@contextmanager
def make_db_connection(host, port, database, query, user, password):
  options: dict[str, Any | None] = {
    "host": host,
    "port": int(port or 5432),
    "database": database,
    "user": user or "postgres",
    "password": password,
    **(query or {}),
  }
  conn = pg8000.connect(**remove_nones_mapping(options))
  try:
    conn.autocommit = True
    yield conn
  finally:
    conn.close()


def make_produser(host, port, database, query, produser, produser_password, superuser=None, superuser_password=None):
  if not produser.isalnum():
    raise Exception(f"Invalid username: {produser}")

  with make_db_connection(host, port, database, query=query, user=superuser, password=superuser_password) as conn:
    with conn.cursor() as cursor:
      execute_create_user_query(
        conn=conn,
        cursor=cursor,
        user=produser,
        password=produser_password,
      )

      # We only grant non-delete privileges to the user, unless the table is allow_listed
      execute_query(
        conn=conn,
        cursor=cursor,
        query_string=f"GRANT SELECT, UPDATE, INSERT ON ALL TABLES IN SCHEMA public TO {produser}",
      )
      execute_query(
        conn=conn, cursor=cursor, query_string=f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {produser}"
      )

      for table in DELETE_ALLOW_LIST:
        execute_query(conn=conn, cursor=cursor, query_string=f"GRANT DELETE ON {table} TO {produser}")


def execute_create_user_query(conn, cursor, user, password, roles=""):
  if password is None:
    query_string = f"CREATE ROLE {user} WITH LOGIN {roles}"
  else:
    psql_password = password.replace("'", "''")
    query_string = f"CREATE ROLE {user} WITH LOGIN PASSWORD '{psql_password}' {roles}"
  return execute_query(
    conn=conn,
    cursor=cursor,
    query_string=query_string,
    error_allow_list=[
      dict(error_str="already exists", warning=f'role: "{user}" already exists. Existing role will be used.')
    ],
  )


def execute_query(conn, cursor, query_string, query_args=None, error_allow_list=None):
  try:
    cursor.execute(query_string, query_args) if query_args else cursor.execute(query_string)
  except pg8000.core.ProgrammingError as error:
    if error_allow_list:
      for e in error_allow_list:
        if e.get("error_str") in str(error):
          logging.warning(e.get("warning"))
          conn.rollback()
          return False
    raise
  return True
