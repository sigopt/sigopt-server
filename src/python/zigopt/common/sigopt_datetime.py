# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
import os
from typing import Optional as _Optional

import pytz


# sigoptlint: disable=AvoidDatetimeNowRule


def default_timezone() -> datetime.tzinfo:
  if os.environ.get("USE_SYSTEM_TIMEZONE") == "1":
    tz = datetime.datetime.now().astimezone().tzinfo
    assert tz
    return tz
  return pytz.utc


def datetime_to_seconds(dt: datetime.datetime, with_microseconds: bool = False) -> int | float:
  try:
    delta = (dt - unix_epoch()).total_seconds()
  except TypeError:
    delta = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
  if not with_microseconds:
    delta = int(delta)
  return delta


def seconds_to_datetime(seconds_since_epoch: float) -> datetime.datetime:
  return datetime.datetime.fromtimestamp(seconds_since_epoch, tz=default_timezone())


def unix_epoch() -> datetime.datetime:
  return datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc).astimezone(default_timezone())


def aware_datetime_to_naive_datetime(dt: datetime.datetime) -> datetime.datetime:
  assert dt.tzinfo is not None
  return dt.astimezone(default_timezone()).replace(tzinfo=None)


def naive_datetime_to_aware_datetime(dt: datetime.datetime) -> datetime.datetime:
  assert dt.tzinfo is None
  return dt.replace(tzinfo=default_timezone())


def current_datetime() -> datetime.datetime:
  return datetime.datetime.now(tz=default_timezone())


def unix_timestamp() -> int:
  return int(datetime_to_seconds(current_datetime(), with_microseconds=True))


def unix_timestamp_with_microseconds() -> float:
  return int(datetime_to_seconds(current_datetime(), with_microseconds=True))


def get_month_interval(dt: _Optional[datetime.datetime] = None) -> tuple[datetime.datetime, datetime.datetime]:
  if dt is None:
    dt = current_datetime()
  start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
  try:
    end = start.replace(month=start.month + 1)
  except ValueError:
    end = start.replace(year=start.year + 1, month=1)
  return start, end


def seconds_until_next_interval(interval_length_seconds: float) -> float:
  # This does its best to make sure that the loop runs once each interval, even
  # if an individual iteration takes an unpredictable amount of time.
  now = unix_timestamp()
  seconds_into_interval = now % interval_length_seconds
  return interval_length_seconds - seconds_into_interval
