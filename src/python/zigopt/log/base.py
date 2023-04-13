# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json
import logging
import logging.handlers
import time
import warnings

from zigopt.common import *


COMPACT_FORMATTER = logging.Formatter("[%(process)d]:%(asctime)s:%(levelname)s:%(name)s:%(message)s")


class JsonFormatter(logging.Formatter):
  converter = time.gmtime

  def __init__(self, environment=None):
    super().__init__()
    self.defaults = dict(environment=environment or "unknown")

  def format_json_message(self, json_message):
    return json_message

  def format(self, record):
    message = record.getMessage()

    # Avoid exceptions from logging messages that are too long.
    # There's probably some way to do this in rsyslog.conf instead?
    message = message[:900]

    log_data = self.defaults.copy()

    log_data.update(
      {
        "level": record.levelname,
        "loggerName": record.name,
        "message": message,
        "pid": record.process,
        "time": self.formatTime(record),
      }
    )

    for record_attr, log_key in [
      ("client_id", "clientId"),
      ("request_id", "requestId"),
      ("query_time", "queryTime"),
      ("status", "status"),
      ("trace_id", "traceId"),
      ("user_id", "userId"),
    ]:
      try:
        value = getattr(record, record_attr, None)
        log_data[log_key] = value
      except AttributeError:
        pass

    if hasattr(record, "request") and record.request is not None:
      request = record.request

      log_data.update(
        {
          "requestId": str(request.id),
          "traceId": str(request.trace_id),
          "requestMethod": request.method,
          "requestURI": request.path,
        }
      )

      try:
        log_data["requestParamsStr"] = json.dumps(request.sanitized_params())
      except Exception as e:  # pylint: disable=broad-except
        if "json" in str(e).lower():
          log_data["requestParamsInvalidJSON"] = True
        else:
          raise

    json_str = json.dumps(log_data)
    return self.format_json_message(json_str)


class SyslogFormatter(JsonFormatter):
  def format_json_message(self, json_message):
    return f"Python: {json_message}"


def sensitive_filter(record):
  return not record.name.startswith("sigopt.rawsql")


def set_default_formatter(formatter):
  root_logger = logging.getLogger()
  default_handler = list_get(root_logger.handlers, 0)
  if default_handler:
    default_handler.setFormatter(formatter)


def base_logger_setup():
  logging.basicConfig()
  set_default_formatter(JsonFormatter())
  configure_warnings()


def syslog_logger_setup(config_broker, syslog_host=None, syslog_port=None):
  syslog_host = syslog_host or "localhost"
  syslog_port = syslog_port or 514

  syslog_handler = None
  if config_broker.get("logging.syslog", default=True):
    syslog_handler = logging.handlers.SysLogHandler(address=(syslog_host, syslog_port))
    if syslog_handler:
      # syslog_handler logs get saved forever, so we make sure
      # we aren't logging anything sensitive here
      syslog_handler.addFilter(sensitive_filter)
      syslog_handler.setFormatter(
        SyslogFormatter(
          environment=config_broker.get("logging.environment", None),
        )
      )
      logging.getLogger().addHandler(syslog_handler)
  return syslog_handler


def configure_warnings():
  logging.captureWarnings(True)
  warnings.filterwarnings("ignore", message="size changed, may indicate binary incompatibility")
  warnings.filterwarnings("default", category=DeprecationWarning, module="sigopt", append=True)


def configure_loggers(config_broker):
  syslog_handler = syslog_logger_setup(config_broker)

  force_level = config_broker.get_int("logging.force")
  if force_level:
    LOG_LEVELS = {"": force_level}
  else:
    LOG_LEVELS = {
      "": logging.WARNING,
      "boto3": logging.WARNING,
      "botocore": logging.WARNING,
      "botocore.vendored.requests.packages.urllib3": logging.WARNING,
      "gunicorn": logging.WARNING,
      "libsigopt.compute.timing": logging.INFO,
      "requests.packages.urllib3": logging.INFO,
      "sigopt": logging.INFO,
      "sigopt.apiexception": logging.INFO,
      "sigopt.config": logging.INFO,
      "sigopt.queue.workers": logging.INFO,
      "sigopt.rawsql": logging.INFO,
      "sigopt.rawsql.timing": logging.INFO,
      "sigopt.requests": logging.INFO,
      "sigopt.sql": logging.INFO,
      "sigopt.timing": logging.INFO,
      "sigopt.www": logging.INFO,
      "urllib3": logging.INFO,
      "werkzeug": logging.WARNING,
    }
    LOG_LEVELS.update(config_broker.get("logging.levels", default={}))

  for name, level in LOG_LEVELS.items():
    logging.getLogger(name or None).setLevel(level)

  # ensure sql goes to syslog only
  if syslog_handler:
    logging.getLogger("sigopt.sql").addHandler(syslog_handler)
  logging.getLogger("sigopt.sql").propagate = False
  if config_broker.get("logging.warnings", "ignore") == "error":
    warnings.simplefilter("error", append=True)

  log_format = config_broker.get_string("logging.format", "verbose")
  if log_format == "compact":
    set_default_formatter(COMPACT_FORMATTER)
  elif log_format == "json":
    set_default_formatter(
      JsonFormatter(
        environment=config_broker.get("logging.environment", None),
      )
    )
