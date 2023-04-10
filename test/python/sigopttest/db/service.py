# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import mock
import pytest

from zigopt.common import *
from zigopt.db.service import DatabaseConnection, DatabaseConnectionService

from sigopttest.base.config_broker import StrictAccessConfigBroker


USERNAME = "fakeproduser"
PASSWORD = "fakepassword"
HOST = "fake.path.to.postgres.com.localhost"
PORT = 5435
PATH = "fakedb"

CONFIG = {
  "enabled": True,
  "user": USERNAME,
  "password": PASSWORD,
  "host": HOST,
  "port": PORT,
  "path": PATH,
  "ssl": False,
  "scheme": "postgresql+pg8000",
}


class TestDatabaseConnectionService:
  @pytest.fixture
  def services(self):
    services = mock.Mock()
    return services

  @pytest.fixture
  def service(self, services):
    return DatabaseConnectionService(services)

  def test_make_engine(self, service):
    engine = service.make_engine(CONFIG)
    assert engine.url.username == USERNAME
    assert engine.url.password == PASSWORD
    assert engine.url.host == HOST
    assert engine.url.port == PORT
    assert engine.url.database == PATH

  def test_override_host_port(self, service):
    engine = service.make_engine(CONFIG, host="other-host", port=9999)
    assert engine.url.username == USERNAME
    assert engine.url.password == PASSWORD
    assert engine.url.host == "other-host"
    assert engine.url.port == 9999
    assert engine.url.database == PATH

  def test_override_user_password(self, service):
    engine = service.make_engine(CONFIG, user="other-user", password="other-password")
    assert engine.url.username == "other-user"
    assert engine.url.password == "other-password"
    assert engine.url.host == HOST
    assert engine.url.port == PORT
    assert engine.url.database == PATH

  def test_connection(self, service, services):
    config_broker = StrictAccessConfigBroker.from_configs({"db": CONFIG})
    engine = service.make_engine(config_broker.get_object("db"))
    assert engine.url.username == USERNAME
    assert engine.url.password == PASSWORD
    assert engine.url.host == HOST
    assert engine.url.port == PORT
    assert engine.url.database == PATH
    connection = DatabaseConnection(engine)
    assert connection.engine is engine

  def test_warmup(self, service, services):
    class OurException(Exception):
      pass

    services.config_broker = StrictAccessConfigBroker.from_configs(
      {
        "db": CONFIG,
      }
    )
    with mock.patch("pg8000.connect", side_effect=OurException()):
      with pytest.raises(OurException):
        service.warmup_db()
