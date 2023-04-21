# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import logging
import ssl
import time
from datetime import timedelta

from sqlalchemy import create_engine, event, inspect, literal, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import DatabaseError, OperationalError, StatementError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import instance_state
from sqlalchemy.orm.exc import NO_STATE, MultipleResultsFound, NoResultFound
from sqlalchemy.sql import text

import zigopt.db.all_models as _all_models  # pylint: disable=unused-import
from zigopt.common import *
from zigopt.services.base import Service


del _all_models


DEFAULT_POOL_RECYCLE_TIME = timedelta(minutes=5).total_seconds()
_TOLERATED_ERRORS = tuple([DatabaseError, OperationalError])


class DatabaseConnection:
  def __init__(self, engine, logger_factory=None):
    self.engine = engine
    self._logger_factory = logger_factory or logging
    self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
    event.listen(self.engine, "before_cursor_execute", self.before_cursor_execute)
    event.listen(self.engine, "after_cursor_execute", self.after_cursor_execute)

  @property
  def _read_logger(self):
    return self._logger_factory.getLogger("sigopt.sql.read")

  @property
  def _write_logger(self):
    return self._logger_factory.getLogger("sigopt.sql")

  # senstive_logger is what gets backed up and logged permanently
  # we are very careful to never log anything senstive to sensitive_logger, but where possible we still want
  # to avoid logging credentials to logger as well. but it is helpful to be able to inspect in more detail what's
  # happening in prod. so we use some heuristics below to try to detect sensitive values
  @property
  def _sensitive_logger(self):
    return self._logger_factory.getLogger("sigopt.rawsql")

  @property
  def _timing_logger(self):
    return self._logger_factory.getLogger("sigopt.rawsql.timing")

  def test(self):
    session = self.create_session()
    try:
      session.execute("SELECT 1 AS connection_test;")
    finally:
      session.close()

  def create_session(self):
    return self._session_factory()

  def close_session(self, session):
    session.close()

  def before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
    del executemany
    params_to_log = self.sanitized_params(parameters)
    conn.info.setdefault("query_start_time", []).append(time.time())
    self._sensitive_logger.debug("%s\n%s", statement, params_to_log)

  def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
    del executemany
    total = time.time() - conn.info["query_start_time"].pop(-1)
    total_ms = total * 1000
    query_logger = self._read_logger if statement.startswith("SELECT ") else self._write_logger
    query_logger.info("%s", statement, extra={"query_time": total_ms})
    self._timing_logger.debug("%s ms", total_ms)

  def sanitized_params(self, params):
    def _sanitized_params(params_to_log):
      if is_sequence(params_to_log):
        return [_sanitized_params(p) for p in params_to_log]
      if is_mapping(params_to_log):
        # a hacky way to avoid logging authentication tokens to the prod machines. could this be done better?
        return {
          key: _sanitized_params(value) if not is_likely_random_string(value) else "****"
          for key, value in params_to_log.items()
        }
      return params_to_log

    return _sanitized_params(params)


class DatabaseConnectionService(Service):
  @classmethod
  def make_engine(cls, config, poolclass=None, **kwargs):
    config = extend_dict({}, config, kwargs)
    echo = config.get("echo", False)
    ssl_context = config.get("ssl_context", None)

    use_ssl = config.get("ssl", True)
    connect_args = {}
    context_to_use = ssl_context or ssl.create_default_context()
    connect_args = {"ssl_context": context_to_use if use_ssl else None}

    override_pool_kwargs: dict = remove_nones_mapping(dict(poolclass=poolclass))
    default_pool_kwargs = dict(
      # Maximum number of persistent connections this engine will keep in the pool, reusing until pool_recycle seconds
      # This is per-process (and only used by code that takes advantage of threading, such as API but not QWorker)
      pool_size=config.get("pool_size", 30),
      # we'd rather not waste time building and tearing down ephemeral connections
      max_overflow=0,
      # Timeout in seconds after which the Engine will automatically close
      # connections. -1 means do this never.
      pool_recycle=config.get("pool_recycle", DEFAULT_POOL_RECYCLE_TIME),
    )
    pool_kwargs = override_pool_kwargs or default_pool_kwargs

    return create_engine(
      URL(
        "postgresql+pg8000",
        username=config.get("user", "postgres"),
        password=config.get("password"),
        host=config.get("host"),
        port=config.get("port"),
        database=config.get("path"),
        query=config.get("query"),
      ),
      connect_args=connect_args,
      execution_options={
        "autocommit": True,
      },
      **pool_kwargs,
      echo=echo,
    )

  def warmup_db(self):
    if self.services.config_broker.get("db.enabled", True):
      config = self.services.config_broker.get("db")
      db_connection = DatabaseConnection(
        self.make_engine(config),
        logger_factory=self.services.logging_service,
      )
      db_connection.test()
      return db_connection
    return None


def sanitize_errors(func):
  # SQLAlchemy includes the full statement and params in the exception error message, so we strip those out
  # so it can be logged safely
  def wrapper(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except StatementError as e:
      try:
        e.params = None
      except AssertionError:
        raise
      except Exception:  # pylint: disable=broad-except
        pass
      raise

  return wrapper


# Retries the query if there is a DB connection error. Only appropriate for read-only functions, otherwise
# we could potentially write data twice.
def retry_on_error(func):
  def wrapper(self, *args, **kwargs):
    with self.services.exception_logger.tolerate_exceptions(_TOLERATED_ERRORS):
      return func(self, *args, **kwargs)
    self.rollback_session()
    return func(self, *args, **kwargs)

  return wrapper


class DatabaseService(Service):
  # pylint: disable=too-many-public-methods

  def __init__(self, services, connection):
    super().__init__(services)
    self._session = None
    self._connection = connection
    self._in_transaction = False
    self._flush_after_writes = True

  @property
  def engine(self):
    return self._connection.engine

  def execute(self, stmt, **kwargs):
    return self.engine.execute(stmt, **kwargs)

  def start_session(self):
    if self._session is not None:
      raise Exception("Started redundant session")
    self._session = self._connection.create_session()

  def end_session(self):
    if self._session:
      self._connection.close_session(self._session)
    self._session = None
    self._in_transaction = False

  # NOTE: Usually SQL databases will give you an error if you try to insert
  # duplicate items. SQLAlchemy was digesting detached ORM objects pulled from DB when we tried to
  # insert them rather than throwing an error. This is because self._session.add(obj)
  # is (almost) a noop when obj._sa_instance_state (has a key and is not attached) == detached
  # https://github.com/zzzeek/sqlalchemy/blob/dd755ca59b173dfd94c7198557553604ccdfa1c2/lib/sqlalchemy/orm/state.py#L227
  def _ensure_safe_to_insert(self, obj):
    if inspect(obj).detached:
      msg = (
        "Cannot insert a detached ORM object. "
        "This may happen if you try to insert an object that is already present in the SQLAlchemy session. "
        "If this is intentional, you may need to either set `inspect(obj).key = None` "
        "or create a new ORM object based on `obj.__dict__` but excluding `_sa_instance_state` "
        f"on {obj} that was pulled from the DB"
      )
      raise ValueError(msg)

  @sanitize_errors
  def flush_session(self):
    assert self._session is not None
    self._session.flush()

  @sanitize_errors
  def rollback_session(self):
    assert self._session is not None
    self._session.rollback()
    self._session.expunge_all()

  @sanitize_errors
  def insert(self, obj):
    assert self._session is not None
    self._ensure_safe_to_insert(obj)
    self._session.add(obj)
    self._commit()
    self._expunge(obj)

  # NOTE: insert_from should be used when a table's values need to
  # be generated from other rows in that table.
  # The best example of this is when creating compound IDs that only increment within
  # some grouping.
  # Ex. insert by incrementing Experiment.key_2 under the condition that Experiment.key_1 == 0
  #   database_service.insert_from(
  #     Example(key_1=0),
  #     insert_dict={
  #       Example.key_2: func.max(Example.key_2) + 1,
  #     },
  #     returning=Example.key_2,
  #     where_clause=lambda q: q.where(Example.key_1 == 0),
  #   )
  #   returns [(X,)] where X is the result of the Example.key_2 insert
  @sanitize_errors
  def insert_from(self, obj, insert_dict, returning, where_clause=lambda s: s):
    column_properties = inspect(obj.__class__).column_attrs
    assert [len(prop.columns) == 1 for prop in column_properties]
    columns_and_values = [(prop.columns[0], getattr(obj, prop.key)) for prop in column_properties]
    unique_column_names = {column.name for column, _ in columns_and_values}
    assert all(
      column.name in unique_column_names for column in insert_dict.keys()
    ), f"The keys of the insert_dict must be columns of {obj.__class__.__name__}"
    insert_selects = {column.name: literal(value, type_=column.type) for column, value in columns_and_values}
    insert_selects.update((column.name, value) for column, value in insert_dict.items())
    column_names = list(insert_selects)
    select_clause = select([insert_selects[column_name].label(column_name) for column_name in column_names])
    insert_query = (
      obj.__class__.__table__.insert()
      .returning(returning)
      .from_select(
        column_names,
        where_clause(select_clause),
      )
    )
    results = self.execute(insert_query)
    return results.fetchall()

  # NOTE: skip_none being True means that the columns with None will not be upserted,
  # leaving whatever values that were in the db previously.
  # Given that storing None values can be desirable, skip_none is an optional behaviour.
  @sanitize_errors
  def upsert(self, obj, where=None, skip_none=False):
    column_values = self._get_column_values(obj)
    if skip_none:
      column_values = remove_nones_sequence(column_values)
    self.execute(
      postgresql_insert(obj.__table__)
      .values(**column_values)
      .on_conflict_do_update(
        constraint=obj.__table__.primary_key,
        set_=column_values,
        where=where,
      )
    )
    self._commit()

  def _get_column_values(self, obj):
    column_properties = inspect(obj.__class__).column_attrs
    assert [len(prop.columns) == 1 for prop in column_properties]
    return dict(((prop.columns[0].name, getattr(obj, prop.key)) for prop in column_properties))

  @sanitize_errors
  def reserve_ids(self, sequence_name, count):
    generated_ids = self.execute(
      text("SELECT nextval(:sequence_name) from generate_series(1,:count)"),
      sequence_name=sequence_name,
      count=count,
    ).fetchall()
    self._commit()
    assert len(generated_ids) == count
    assert all(id_x < id_x_plus_1 for id_x, id_x_plus_1 in sliding(generated_ids, 2))
    return [g[0] for g in generated_ids]

  # NOTE: return_defaults means that objects without primary keys
  # are inserted one-at-a-time. This is the most common case and could likely
  # be improved.
  @sanitize_errors
  def insert_all(self, objs, return_defaults=True):
    for obj in objs:
      self._ensure_safe_to_insert(obj)
    if objs:
      assert self._session is not None
      self._session.bulk_save_objects(objs, return_defaults=return_defaults)
      self._commit()

  @sanitize_errors
  def update_all(self, mapper, mappings):
    assert self._session is not None
    self._session.bulk_update_mappings(mapper, mappings)
    self._commit()

  @sanitize_errors
  def query(self, *args):
    assert self._session is not None
    return self._session.query(*args)

  @sanitize_errors
  @retry_on_error
  def first(self, q):
    ret = q.first()
    self._expunge(ret)
    self._rollback()
    return ret

  @sanitize_errors
  @retry_on_error
  def all(self, q):
    ret = q.all()
    for r in ret:
      self._expunge(r)
    self._rollback()
    return ret

  @sanitize_errors
  @retry_on_error
  def one(self, q):
    ret = q.one()
    self._expunge_one(ret)
    self._rollback()
    return ret

  @sanitize_errors
  @retry_on_error
  def one_or_none(self, q):
    ret = q.one_or_none()
    if ret is not None:
      self._expunge_one(ret)
    self._rollback()
    return ret

  @sanitize_errors
  @retry_on_error
  def scalar(self, q):
    return q.scalar()

  # NOTE: q is a nested query, self.query is required to execute the `exists` clause.
  def exists(self, q):
    return self.scalar(self.query(q.exists()))

  # Yields rows while only fetching `batch_size` rows into memory at a time.
  # Returns an iterable that can only be iterated over once
  # NOTE: Read this caveat before using this method
  # http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg12443.html
  @sanitize_errors
  def stream(self, batch_size, q):
    return self._stream_generator(batch_size, q)

  @generator_to_safe_iterator
  def _stream_generator(self, batch_size, q):
    for r in q.yield_per(batch_size):
      self._expunge(r)
      yield r
    self._rollback()

  @sanitize_errors
  @retry_on_error
  def count(self, q):
    ret = q.count()
    self._rollback()
    return ret

  @sanitize_errors
  def delete(self, q):
    return self._commit_modification_if_allowed(
      q.delete(synchronize_session=False),
      allow_more_than_one=True,
      allow_zero=True,
    )

  @sanitize_errors
  def delete_one(self, q):
    return self._commit_modification_if_allowed(
      q.delete(synchronize_session=False),
      allow_more_than_one=False,
      allow_zero=False,
    )

  @sanitize_errors
  def delete_one_or_none(self, q):
    return self._commit_modification_if_allowed(
      q.delete(synchronize_session=False),
      allow_more_than_one=False,
      allow_zero=True,
    )

  @sanitize_errors
  def update(self, q, params):
    return self._commit_modification_if_allowed(
      q.update(params, synchronize_session=False),
      allow_more_than_one=True,
      allow_zero=True,
    )

  @sanitize_errors
  def update_one(self, q, params):
    return self._commit_modification_if_allowed(
      q.update(params, synchronize_session=False),
      allow_more_than_one=False,
      allow_zero=False,
    )

  @sanitize_errors
  def update_one_or_none(self, q, params):
    return self._commit_modification_if_allowed(
      q.update(params, synchronize_session=False),
      allow_more_than_one=False,
      allow_zero=True,
    )

  @sanitize_errors
  def update_returning(self, model, where, values):
    assert self._session is not None
    rows = self._session.execute(update(model).where(where).values(**values).returning(*model.__table__.columns))
    self._commit()

    mapper_attrs = model.__mapper__.attrs
    kwarg_map = {a.key: a.class_attribute.name for a in mapper_attrs}
    objs = [model(**{key: row[value] for key, value in kwarg_map.items()}) for row in rows]
    return objs

  def _commit_modification_if_allowed(self, count, allow_more_than_one, allow_zero):
    assert is_number(count)
    try:
      if not allow_zero:
        self._maybe_raise_no_result_found(count)
      if not allow_more_than_one:
        self._maybe_raise_multiple_results_found(count)
    except (NoResultFound, MultipleResultsFound):
      self._rollback()
      raise
    self._commit()
    return count

  def _maybe_raise_multiple_results_found(self, count):
    if count > 1:
      raise MultipleResultsFound(f"Expected exactly one result - {count} found")

  def _maybe_raise_no_result_found(self, count):
    if count == 0:
      raise NoResultFound("Expected exactly one result - none found")

  def _commit(self):
    if self._in_transaction:
      if self._flush_after_writes:
        self.flush_session()
    else:
      assert self._session is not None
      self._session.commit()

  def _rollback(self):
    if not self._in_transaction:
      assert self._session is not None
      self._session.rollback()

  def _expunge(self, obj):
    if obj:
      if is_sequence(obj):
        for o in obj:
          self._expunge_one(o)
      else:
        self._expunge_one(obj)

  def _expunge_one(self, obj):
    if not self._in_transaction:
      try:
        instance_state(obj)
      except NO_STATE:
        # object not attached to ORM, can't be expunged?
        # this can occur with the dynamically generated class definitions
        # might be better to just make sure those classes' definitions are registered
        pass
      else:
        assert self._session is not None
        self._session.expunge(obj)
