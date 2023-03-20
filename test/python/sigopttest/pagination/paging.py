# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.pagination.paging import *


# Transformation functions that operate on Nones successfully
def nfloat(n):
  return float(n) if n is not None else n


def nint(n):
  return int(n) if n is not None else n


def nidentity(n):
  return n if n is not None else 100001


def Request(*, limit=None, before=None, after=None):
  return PagingRequest(limit=limit, before=before, after=after)


class TestPager(object):
  @pytest.fixture(params=[0, 1, 2, 5, 10, 100])
  def items(self, request):
    return [None] + list(reversed(range(request.param)))

  @pytest.fixture(params=[0, 1, 2, 5, 10, 100])
  def prefix(self, request):
    return request.param

  # Various different mappings from objects to sort fields.
  # We must ensure that sort keys are unique, and the last
  # field is an integer.
  @pytest.fixture(
    params=[
      nidentity,
      lambda n: (n, nidentity(n)),
      lambda n: (n, 1),
      lambda n: (1, nidentity(n)),
      lambda n: (1, 1, 1, 1, nidentity(n)),
      lambda n: (n, 1, 1, 1, 1),
      lambda n: (n, n, n, n, 1),
      lambda n: (nfloat(n), nidentity(n)),
      lambda n: (nint(n), nidentity(n)),
    ]
  )
  def key(self, request):
    return request.param

  def test_list_default(self, items, prefix, key):
    page, _, _ = Pager(items).fetch(Request(limit=prefix), key)
    assert page == items[:prefix]

  def test_list_descending(self, items, prefix, key):
    page, _, _ = Pager(items).fetch(Request(limit=prefix), key, ascending=False)
    assert page == items[:prefix]

  def test_list_ascending(self, items, prefix, key):
    page, _, _ = Pager(items).fetch(Request(limit=prefix), key, ascending=True)
    assert page == list(reversed(items))[:prefix]

  def test_reach_limit(self, items, prefix, key):
    _, before, _ = Pager(items).fetch(Request(limit=prefix), key, ascending=False)
    if prefix >= len(items):
      assert before is None
    else:
      assert before is not None
      assert Pager(items).fetch(Request(limit=1, before=before), key, ascending=False)[0][0] == items[prefix]

  def test_reach_limit_ascending(self, items, prefix, key):
    _, _, after = Pager(items).fetch(Request(limit=prefix), key, ascending=True)
    if prefix >= len(items):
      assert after is None
    else:
      assert after is not None
      assert Pager(items).fetch(Request(limit=1, after=after), key, ascending=True)[0][0] == items[-prefix - 1]

  def test_limit_prefix(self, items, prefix, key):
    page, before, _ = Pager(items).fetch(Request(limit=prefix), key, ascending=False)
    assert page == items[:prefix]
    if before is not None:
      second_page, _, _ = Pager(items).fetch(Request(limit=prefix, before=before), key, ascending=False)
      assert page + second_page == items[: 2 * prefix]
    else:
      assert page == items or prefix == 0

  def test_limit_prefix_ascending(self, items, prefix, key):
    page, _, after = Pager(items).fetch(Request(limit=prefix), key, ascending=True)
    assert page == list(reversed(items))[:prefix]
    if after is not None:
      second_page, _, _ = Pager(items).fetch(Request(limit=prefix, after=after), key, ascending=True)
      assert page + second_page == list(reversed(items))[: 2 * prefix]
    else:
      assert page == list(reversed(items)) or prefix == 0

  def test_returned_before(self, items, prefix, key):
    page, new_before, _ = Pager(items).fetch(Request(limit=prefix), key, ascending=False)
    assert page == items[:prefix]
    if new_before is not None:
      second_page, before1, _ = Pager(items).fetch(Request(before=new_before), key, ascending=False)
      other_page, before2, _ = Pager(second_page).fetch(Request(), key, ascending=False)
      assert second_page == other_page
      assert before1 == before2
      assert page + second_page == items
    else:
      assert page == items or prefix == 0

  def test_returned_after(self, items, prefix, key):
    page, _, new_after = Pager(items).fetch(Request(limit=prefix), key, ascending=False)
    if new_after is not None:
      assert Pager(items).fetch(Request(after=new_after), key, ascending=False)[0] == []
    else:
      assert page == []

  def test_returned_before_ascending(self, items, prefix, key):
    page, new_before, _ = Pager(items).fetch(Request(limit=prefix), key, ascending=True)
    if new_before is not None:
      assert Pager(items).fetch(Request(before=new_before), key, ascending=True)[0] == []
    else:
      assert page == []

  def test_returned_after_ascending(self, items, prefix, key):
    page, _, new_after = Pager(items).fetch(Request(limit=prefix), key, ascending=True)
    assert page == list(reversed(items))[:prefix]
    if new_after is not None:
      second_page, _, after1 = Pager(items).fetch(Request(after=new_after), key, ascending=True)
      other_page, _, after2 = Pager(second_page).fetch(Request(), key, ascending=True)
      assert second_page == other_page
      assert after1 == after2
      assert page + second_page == list(reversed(items))
    else:
      assert page == list(reversed(items)) or prefix == 0
