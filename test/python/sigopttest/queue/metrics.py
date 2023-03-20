# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import mock
import pytest

from zigopt.common.sigopt_datetime import seconds_until_next_interval


INTERVAL_SECONDS = 7


def mock_unix_timestamp(return_value):
  mock_ut = mock.patch("zigopt.common.sigopt_datetime.unix_timestamp", return_value=return_value)
  return mock_ut


@pytest.mark.parametrize(
  "current_timestamp,expected",
  [
    (INTERVAL_SECONDS, INTERVAL_SECONDS),
    (2 * INTERVAL_SECONDS, INTERVAL_SECONDS),
    (2 * INTERVAL_SECONDS + 1, INTERVAL_SECONDS - 1),
    (3 * INTERVAL_SECONDS - 1, 1),
  ],
)
def test_seconds_until_next_interval(current_timestamp, expected):
  with mock_unix_timestamp(current_timestamp):
    assert seconds_until_next_interval(INTERVAL_SECONDS) == expected
