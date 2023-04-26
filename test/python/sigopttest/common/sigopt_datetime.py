# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime as dt
import os
import time

import pytest

from zigopt.common.sigopt_datetime import *


def switch_to_system_timezone():
  os.environ["USE_SYSTEM_TIMEZONE"] = "1"
  time.tzset()


def switch_to_utc(explicit=False):
  if explicit:
    os.environ["USE_SYSTEM_TIMEZONE"] = "1"
    os.environ["TZ"] = "UTC"
  else:
    os.environ["USE_SYSTEM_TIMEZONE"] = "0"
  time.tzset()


BASELINE_EPOCH = dt.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=pytz.utc)


class TestDefaultTimezone:
  @pytest.fixture(autouse=True, params=[True, False])
  def initialize_timezone(self, request):
    switch_to_utc(explicit=request.param)

  def test_current_datetime(self):
    now = current_datetime()
    assert now.tzinfo
    assert now.tzinfo.tzname(None) == "UTC"

  def test_unix_epoch(self):
    assert unix_epoch() == BASELINE_EPOCH
    assert datetime_to_seconds(unix_epoch()) == 0
    assert seconds_to_datetime(0) == unix_epoch()

  def test_aware_datetime_to_naive_datetime(self):
    now = current_datetime()
    assert aware_datetime_to_naive_datetime(now) == now.replace(tzinfo=None)
    assert aware_datetime_to_naive_datetime(
      dt.datetime(1989, 8, 12, 0, tzinfo=pytz.timezone("Etc/GMT+12"))
    ) == dt.datetime(year=1989, month=8, day=12, hour=12, minute=0, tzinfo=None)

  def test_naive_datetime_to_aware_datetime(self):
    now = current_datetime()
    assert naive_datetime_to_aware_datetime(now.replace(tzinfo=None)) == now
    assert naive_datetime_to_aware_datetime(dt.datetime(1989, 8, 12, 0, tzinfo=None)) == dt.datetime(
      1989, 8, 12, 0, tzinfo=pytz.UTC
    )


class TestSystemTimezone:
  @pytest.fixture(autouse=True)
  def initialize_timezone(self):
    os.environ["TZ"] = "Etc/GMT+12"
    switch_to_system_timezone()
    yield
    switch_to_utc()

  def test_current_datetime(self):
    now = current_datetime()
    assert now.tzinfo
    assert now.tzinfo.tzname(None) == "-12"

  def test_unix_epoch(self):
    assert unix_epoch() == BASELINE_EPOCH
    assert datetime_to_seconds(unix_epoch()) == 0
    assert seconds_to_datetime(0) == unix_epoch()

  def test_aware_datetime_to_naive_datetime(self):
    now = current_datetime()
    assert aware_datetime_to_naive_datetime(now) == now.replace(tzinfo=None)
    assert aware_datetime_to_naive_datetime(dt.datetime(1989, 8, 12, 0, tzinfo=pytz.timezone("UTC"))) == dt.datetime(
      year=1989, month=8, day=11, hour=12, tzinfo=None
    )

  def test_naive_datetime_to_aware_datetime(self):
    now = current_datetime()
    assert naive_datetime_to_aware_datetime(now.replace(tzinfo=None)) == now
    assert naive_datetime_to_aware_datetime(dt.datetime(1989, 8, 12, 0, tzinfo=None)) == dt.datetime(
      1989, 8, 12, 0, tzinfo=default_timezone()
    )


@pytest.mark.parametrize(
  "date,expected_start,expected_end",
  [
    ("2022-01-01", "2022-01-01", "2022-02-01"),
    ("2022-01-15", "2022-01-01", "2022-02-01"),
    ("2022-01-31", "2022-01-01", "2022-02-01"),
    ("2022-12-01", "2022-12-01", "2023-01-01"),
    ("2024-02-29", "2024-02-01", "2024-03-01"),
  ],
)
def test_month_interval(date, expected_start, expected_end):
  date, *expected_interval = (dt.datetime.fromisoformat(d) for d in (date, expected_start, expected_end))
  interval = get_month_interval(date)
  assert interval == tuple(expected_interval)
