# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from sqlalchemy.sql.functions import coalesce as sql_coalesce

from zigopt.common import generator_to_safe_iterator, is_mapping
from zigopt.db.column import adapt_for_jsonb


# customlint: disable=AccidentalFormatStringRule


@generator_to_safe_iterator
def get_json_paths_and_values(merge_objects, attribute, value):
  """
    Returns a list of JSON paths and the values they should be set to.
    This is because postgres will not create intermediary keys if you
    are setting a deeply nested JSON value. So, when MERGEing we have to
    recursvively iterate through the JSON object and create the necessary
    paths in order
    So, if we want to merge in a value {"a": {"b": 1, "c": 2}}, we need to emit:

    jsonb_set(data, '{a}', coalesce(data -> 'a', '{}'))
    jsonb_set(data, '{a,b}', 1)
    jsonb_set(data, '{a,c}', 2)
    """

  if is_mapping(value) and merge_objects:
    yield (attribute, sql_coalesce(attribute, adapt_for_jsonb({})))
    for field_name, subvalue in value.items():
      yield from get_json_paths_and_values(merge_objects, attribute[field_name], subvalue)
  else:
    yield (attribute, value)
