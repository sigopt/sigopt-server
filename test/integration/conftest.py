# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import os

import backoff
import mock
import pytest
import redis
import requests
import werkzeug

from zigopt.common import *
from zigopt.config.broker import ConfigBroker
from zigopt.profile.profile import NullProfiler, Profiler
from zigopt.queue.message_groups import MessageGroup
from zigopt.services.api import ApiRequestLocalServiceBag, ApiServiceBag

from integration.auth import AuthProvider
from integration.base import BaseTest
from integration.utils.wait import wait_for


# This hook is used to detect if the test is very slow
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
  allow_slow = bool(os.environ.get("ALLOW_SLOW"))
  outcome = yield
  if not allow_slow:
    result = outcome.get_result()
    if result.duration > 20 and result.when == "call" and result.outcome == "passed" and not item.keywords.get("slow"):
      result.outcome = "failed"
      result.longrepr = "Very slow test, add pytest.mark.slow if this is intentional"


def wait_for_url(url, proc=None, seconds=10, raise_for_status=False):
  @backoff.on_exception(
    backoff.expo,
    (requests.ConnectionError, requests.exceptions.HTTPError),
    max_time=seconds,
  )
  def waiter():
    if proc and proc.poll() is not None:
      raise Exception(f"{url} failed on startup!")
    response = requests.head(url, verify=os.environ.get("SIGOPT_API_VERIFY_SSL_CERTS", True), timeout=5)
    if raise_for_status:
      response.raise_for_status()

  try:
    return waiter()
  except Exception as e:
    raise Exception(f"{url} did not start") from e


@pytest.fixture(scope="session", autouse=True)
def profiler(request):
  profile = request.config.option.profile
  profiler = Profiler() if profile else NullProfiler()
  profiler.enable()
  yield profiler
  profiler.disable()
  profiler.print_stats()


@pytest.fixture(scope="session")
def config_broker(request):
  config_file = request.config.getoption("--config-file")
  return ConfigBroker.from_file(config_file)


@pytest.fixture(scope="session")
def api_url(config_broker):
  return BaseTest.get_api_url(config_broker)


@pytest.fixture(scope="session")
def app_url(config_broker):
  return BaseTest.get_app_url(config_broker)


@pytest.fixture(scope="function")
def auth_provider(config_broker, db_connection, api, inbox, services):
  # Depends on inbox because creating new users sends email
  api_url = BaseTest.get_api_url(config_broker)
  return AuthProvider(config_broker, db_connection, api_url, services)


@pytest.fixture(scope="session", autouse=True)
def redis_server(config_broker):
  yield


@pytest.fixture(scope="session")
def global_services(config_broker, email_server, redis_server):
  del email_server
  del redis_server
  # depends on redis_server being started
  return ApiServiceBag(config_broker, is_qworker=False)


@pytest.fixture
def services(global_services, config_broker):
  ret = ApiRequestLocalServiceBag(global_services)

  # In case the test modifies the service bag with mocks pull the references we need
  # here so that the cleanup code is guaranteed to refer to the same objects
  database_service = ret.database_service
  redis_service = ret.redis_service
  redis_enabled = redis_service.enabled

  database_service.start_session()
  redis_service.warmup()
  try:
    yield ret
  finally:
    database_service.end_session()
    if redis_enabled:
      try:
        redis_service.dangerously_purge_database()
      except redis.exceptions.ConnectionError:
        pass


def wait_for_messages_to_finish(global_services, queue_name, timeout=60):
  return wait_for(
    lambda: sum(
      [
        global_services.queue_service.count_queued_messages(queue_name),
        global_services.message_tracking_service.count_processing_messages(queue_name),
      ]
    )
    == 0,
    timeout_message=f"Timed out waiting messages to finish in {queue_name}",
    timeout=timeout,
  )


@pytest.fixture(scope="function")
def wait_for_empty_optimization_queue(global_services):
  def waiter(timeout=60):
    return wait_for_messages_to_finish(
      global_services,
      global_services.config_broker["queue.message_groups.optimization.pull_queue_name"],
      timeout=timeout,
    )

  return waiter


@pytest.fixture(scope="function")
def wait_for_empty_analytics_queue(global_services):
  return lambda: wait_for_messages_to_finish(
    global_services,
    global_services.config_broker["queue.message_groups.analytics.pull_queue_name"],
  )


@pytest.fixture(scope="function")
def db_connection(services):
  return services.database_service


@pytest.fixture(scope="function")
def payment_service(services):
  return services.payment_service


@pytest.fixture(scope="function")
def web(config_broker):
  wait_for_url(config_broker["address.app_url"], seconds=300, raise_for_status=True)
  yield None


# NOTE: we include services here to make sure redis doesn't get purged before we check for unprocessed messages
@pytest.fixture(autouse=True, scope="function")
def wait_for_queue_cleanup(global_services, services):
  yield
  for message_group in MessageGroup:
    queue_name = global_services.message_router.get_queue_name_from_message_group(message_group)
    if queue_name is None:
      continue
    try:
      wait_for_messages_to_finish(global_services, queue_name)
    except TimeoutError as e:
      raise TimeoutError(
        f"Timed out waiting for all messages in {message_group} to process."
        f" This might indicate that the worker for {message_group} exited pre-maturely."
        " Look for the first failing test and worker logs to debug the issue."
      ) from e


@pytest.fixture(scope="session")
def api(request, config_broker, email_server, api_url):
  del email_server
  wait_for_url(f"{api_url}/health")
  yield


@pytest.fixture(scope="session")
def email_enabled(config_broker):
  return config_broker.get("email.enabled", True)


@pytest.fixture(scope="session")
def base_email_url(config_broker, email_enabled):
  base_url = None
  if email_enabled:
    receive_host = config_broker["smtp.receive_host"]
    receive_port = int(config_broker["smtp.receive_port"])
    base_url = f"http://{receive_host}:{receive_port}"
  return base_url


@pytest.fixture(scope="session")
def email_server(config_broker, email_enabled, base_email_url):
  base_url = base_email_url
  if email_enabled:
    wait_for_url(f"{base_url}/health")


@pytest.fixture(scope="function")
def base_inbox(email_server, email_enabled, base_email_url, config_broker, wait_for_empty_analytics_queue):
  del email_server
  del wait_for_empty_analytics_queue
  enabled = email_enabled
  base_url = base_email_url

  class EmailInbox(object):
    def reset(self):
      if enabled:
        requests.post(f"{base_url}/reset", timeout=5).raise_for_status()

    def _list_email_messages(self, email):
      response = requests.get(f"{base_url}/message/{email}/list", timeout=5)
      response.raise_for_status()
      return [email_message.get("message") or {} for email_message in response.json()]

    def check_email(self, email, search_term=None):
      if not enabled:
        pytest.skip()
      messages = self._list_email_messages(email)
      return [
        message.get("body") for message in messages if search_term is None or search_term in message.get("body", "")
      ]

    def wait_for_email(self, email, search_term=None):
      try:
        return wait_for(lambda: self.check_email(email, search_term))
      except TimeoutError as e:
        raise TimeoutError(f"Timed out waiting for emails for {email} with search term {repr(search_term)}") from e

  return EmailInbox()


@pytest.fixture(scope="session", autouse=True)
def check_for_deep_mocked_services(global_services):
  yield

  if recursively_check_for_instances(
    global_services, check=(mock.Mock, mock.MagicMock), ignore=(werkzeug.local.LocalProxy)
  ):
    raise Exception(
      "Detected a test that has a Mock or MagicMock that leaks between tests."
      " Prefer mock.patch.object for mocking global services."
    )


@pytest.fixture(scope="function")
def inbox(base_inbox):
  if base_inbox:
    base_inbox.reset()
  return base_inbox


def pytest_addoption(parser):
  parser.addoption(
    "--config-file",
    help="config json file for db",
  )

  parser.addoption(
    "--skip-compile",
    action="store_true",
    help="skip compiling css and javascript.",
  )

  parser.addoption(
    "--profile",
    action="store_true",
    help="run the profiler",
  )
