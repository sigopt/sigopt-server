# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy import asc, desc, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.expression import tuple_

from zigopt.common import *
from zigopt.net.errors import BadParamError
from zigopt.pagination.lib import get_value_of_paging_symbol
from zigopt.pagination.paging import Pager
from zigopt.protobuf.gen.api.paging_pb2 import PagingMarker
from zigopt.services.base import Service


class QueryPager(Service):
  def get_page_results(
    self,
    q,
    Fields,
    limit,
    before,
    after,
    ascending=False,
    use_having=False,
    nulls_descendant=False,
  ):
    # pylint: disable=too-many-locals
    Fields = as_tuple(Fields)
    assert isinstance(before, (type(None), PagingMarker))
    assert isinstance(after, (type(None), PagingMarker))

    # The query is restricted to only return results within the provided pagination bounds.
    # By default, this is done by adding the bounds to the WHERE clause.
    # This only works if the pagination bounds apply to fields that are available in the WHERE context.
    # If you want to paginate based on an aggregated field (such as a max or count), you may need to use HAVING,
    # which can be applied after aggregate functions have been computed.
    # See https://www.postgresql.org/docs/11/tutorial-agg.html for the difference between WHERE and HAVING
    def having(q, clause):
      if use_having:
        return q.having(clause)
      return q.filter(clause)

    def marker_to_rhs(marker):
      if len(Fields) != len(marker.symbols):
        raise BadParamError("Invalid paging marker")
      compare_values = (get_value_of_paging_symbol(s) for s in marker.symbols)
      casted_values = (func.cast(v, JSONB) if isinstance(F.type, JSONB) else v for F, v in zip(Fields, compare_values))
      return tuple_(*casted_values)

    if before is not None:
      q = having(q, tuple_(*Fields) < marker_to_rhs(before))

    if after is not None:
      q = having(q, tuple_(*Fields) > marker_to_rhs(after))

    if ascending:
      start_from_before = before is not None and after is None
    else:
      start_from_before = before is not None or after is None

    for F in Fields:
      # https://www.postgresql.org/docs/11/queries-order.html
      #   > The NULLS FIRST and NULLS LAST options can be used to determine whether nulls appear before
      #   > or after non-null values in the sort ordering. By default, null values sort as if larger
      #   > than any non-null value; that is, NULLS FIRST is the default for DESC order, and NULLS LAST otherwise.
      #
      # Set `nulls_descendant=True` to flip this behaviour. It will treat NULLS as though they are descendant,
      # i.e. smaller than any other value
      order_by_clause = desc(F) if start_from_before else asc(F)
      nulls_first = start_from_before ^ nulls_descendant
      order_by_clause = order_by_clause.nullsfirst() if nulls_first else order_by_clause.nullslast()
      q = q.order_by(order_by_clause)

    if limit is not None:
      q = q.limit(limit)

    results = self.services.database_service.all(q)
    if not start_from_before:
      results.reverse()
    return results

  def fetch_page(self, q, Field, paging, use_having=False, ascending=False, nulls_descendant=False):
    single_entity = q.is_single_entity
    Fields = as_tuple(Field)
    Fields = tuple(F.label(f"field_{i}") for i, F in enumerate(Fields))
    q = q.add_columns(*Fields)

    def page_fetcher(limit, before, after):
      return self.get_page_results(
        q,
        Fields,
        limit=limit,
        before=before,
        after=after,
        use_having=use_having,
        ascending=ascending,
        nulls_descendant=nulls_descendant,
      )

    def untuple_result(result):
      result = result[: -len(Fields)]
      if single_entity:
        assert len(result) == 1
        return result[0]
      return result

    results_with_sort_fields, before, after = Pager(page_fetcher).fetch(paging, Fields, ascending=ascending)
    results = [untuple_result(r) for r in results_with_sort_fields]
    return results, before, after
