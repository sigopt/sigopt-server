# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime as dt

from zigopt.common import *
from zigopt.common.sigopt_datetime import aware_datetime_to_naive_datetime
from zigopt.common.struct import ImmutableStruct
from zigopt.pagination.lib import get_value_of_paging_symbol
from zigopt.protobuf.gen.api.paging_pb2 import PagingMarker, PagingSymbol
from zigopt.protobuf.lib import copy_protobuf


SortRequest = ImmutableStruct("SortRequest", ("field", "ascending"))
PagingRequest = ImmutableStruct("PagingRequest", ("limit", "before", "after"))

INF = float("inf")


class Pager:
  """
    This class handles all the logic for paginating queries. Given a result set
    and a (limit, before, after) tuple, it returns the corresponding page
    from that result set.

    The result set can either be a function that takes (limit, before, after)
    and returns results (typically an API query), or it can be a list.

    Results are sorted by a field (or a list of fields). This can be provided
    as a SQLAlchemy database field (such as Experiment.id), or a function
    that returns the field(s) on that object. When sorting on a list of fields,
    results are compared by the first field, then the second field, and so on.

    This class consumes before/after markers (used to define the current page
    of results) and emits new before/after markers (for the next page). The
    client should treat these markers as opaque strings. Internally, these
    strings are comma-separated values for each of the sort fields.
    """

  # We use _NO_MARKER to indicate when the client has not provided bounds,
  # or to return to the client that there are no more results. We do not
  # use None - this is because the results we are sorting could contain
  # None values. This comes up when paging over sorted observations values,
  # which can be None on failed observations.
  _NO_MARKER = object()
  item_list: list | None

  def __init__(self, fetch_page):
    try:
      self.item_list = list(fetch_page)
      self.fetch_page = None
    except TypeError:
      self.item_list = None
      self.fetch_page = fetch_page

  def _sanitize_marker(self, field_value):
    if field_value is self._NO_MARKER:
      return None
    return field_value

  # Increment/Decrement marker returns the marker immediately before or after
  # this marker. This is so the user can page back to the page they were
  # previously on.
  # NOTE: We use +1 / -1 because we assume we are always using an
  # integer ID as a tie-breaker. If the tie breaker can be a floating point
  # value, we should use numpy.nextafter.
  def _increment_marker(self, marker):
    assert marker.symbols[-1].WhichOneof("type") == "int_value"
    marker = copy_protobuf(marker)
    marker.symbols[-1].int_value += 1
    return marker

  def _decrement_marker(self, marker):
    assert marker.symbols[-1].WhichOneof("type") == "int_value"
    marker = copy_protobuf(marker)
    marker.symbols[-1].int_value -= 1
    return marker

  def _get_field_values_from_result(self, Field, r):
    if hasattr(Field, "__call__"):
      return as_tuple(Field(r))
    Fields = as_tuple(Field)
    ret = []
    for F in Fields:
      ret.append(getattr(r, F.name))
    return tuple(ret)

  def _build_marker_from_field_values(self, field_values):
    marker = PagingMarker()
    for value in field_values:
      symbol = marker.symbols.add()
      if value is None:
        symbol.null_value = PagingSymbol.NULL_VALUE
        symbol.null_value  # pylint: disable=pointless-statement
      elif isinstance(value, dt.datetime):
        symbol.timestamp_value.FromDatetime(aware_datetime_to_naive_datetime(value))
      elif is_number(value):
        if is_integer(value):
          symbol.int_value = value
          symbol.int_value  # pylint: disable=pointless-statement
        else:
          symbol.double_value = value
          symbol.double_value  # pylint: disable=pointless-statement
      elif is_string(value):
        symbol.string_value = value
        symbol.string_value  # pylint: disable=pointless-statement
      elif is_boolean(value):
        symbol.bool_value = value
        symbol.bool_value  # pylint: disable=pointless-statement
      else:
        raise ValueError(f"Unknown field value: {value}")
    return marker

  @generator_to_list
  def _get_field_values_from_marker(self, marker):
    for s in marker.symbols:
      yield get_value_of_paging_symbol(s)

  def _sanitize_nones(self, val):
    return tuple(coalesce(v, INF) for v in val)

  def _sanitized_field_values_from_result(self, Field, v):
    return self._sanitize_nones(self._get_field_values_from_result(Field, v))

  def _sanitized_field_values_from_marker(self, v):
    return self._sanitize_nones(self._get_field_values_from_marker(v))

  def _fetch_page_from_item_list(self, Field, sorted_list, limit, before, after, start_from_before):
    filtered_page = [
      p
      for p in sorted_list
      if (
        (
          before is self._NO_MARKER
          or self._sanitized_field_values_from_result(Field, p) < self._sanitized_field_values_from_marker(before)
        )
        and (
          after is self._NO_MARKER
          or self._sanitized_field_values_from_result(Field, p) > self._sanitized_field_values_from_marker(after)
        )
      )
    ]
    if limit is not None:
      filtered_page = filtered_page[:limit] if start_from_before else list(tail(filtered_page, limit))
    return filtered_page

  def _get_markers_from_results(self, results, Field, start_from_before, has_more):
    minimum = self._build_marker_from_field_values(self._get_field_values_from_result(Field, results[-1]))
    maximum = self._build_marker_from_field_values(self._get_field_values_from_result(Field, results[0]))

    if start_from_before:
      return (minimum if has_more else self._NO_MARKER, maximum)
    return (minimum, maximum if has_more else self._NO_MARKER)

  def _get_new_markers(self, results, before, after, Field, start_from_before, has_more):
    if results:
      return self._get_markers_from_results(results, Field, start_from_before, has_more)
    if start_from_before:
      return (before, self._increment_marker(before) if before is not self._NO_MARKER else self._NO_MARKER)
    return (self._decrement_marker(after) if after is not self._NO_MARKER else self._NO_MARKER, after)

  def fetch(self, paging, Field, ascending=False):
    # pylint: disable=too-many-locals
    assert isinstance(paging, PagingRequest)
    limit = paging.limit
    before = coalesce(paging.before, self._NO_MARKER)
    after = coalesce(paging.after, self._NO_MARKER)
    assert not isinstance(before, str)
    assert not isinstance(after, str)
    fetch_limit = None if limit is None else limit + 1

    # start_from_before indicates which "direction" to search. When start_from_before
    # is true the first result will be the result immediately before "before". Otherwise
    # it will be the one immediately after "after"
    if ascending:
      start_from_before = before is not self._NO_MARKER and after is self._NO_MARKER
    else:
      start_from_before = before is not self._NO_MARKER or after is self._NO_MARKER

    if self.item_list is None:
      assert self.fetch_page is not None
      # TODO: Most callers of this function are not equipped to handle _NO_MARKER, so we adapt it
      # back into None. But this means that None values will not be sorted properly. Fortunately,
      # for most of those use-cases they are just sorting by ID.
      qbefore = None if before is self._NO_MARKER else before
      qafter = None if after is self._NO_MARKER else after
      results = self.fetch_page(fetch_limit, qbefore, qafter)
    else:
      sorted_list = sorted(
        self.item_list, key=lambda v: self._sanitized_field_values_from_result(Field, v), reverse=True
      )
      results = self._fetch_page_from_item_list(Field, sorted_list, fetch_limit, before, after, start_from_before)

    has_more = fetch_limit is not None and len(results) >= fetch_limit

    # We need to do some special-case handling when the limit is 0.
    # This is a degenerate case but we should handle it properly
    if limit == 0:
      assert len(results) <= 1
      if results:
        extra_item = results[0]
        marker = self._build_marker_from_field_values(self._get_field_values_from_result(Field, extra_item))
        if start_from_before:
          return [], self._sanitize_marker(self._increment_marker(marker)), None
        return [], None, self._sanitize_marker(self._decrement_marker(marker))
      return [], None, None
    if limit is not None:
      results = results[:limit] if start_from_before else tail(results, limit)

    new_before, new_after = self._get_new_markers(results, before, after, Field, start_from_before, has_more)
    if results and ascending:
      results.reverse()

    return results, self._sanitize_marker(new_before), self._sanitize_marker(new_after)
