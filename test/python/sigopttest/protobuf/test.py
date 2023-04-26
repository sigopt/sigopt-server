# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# pylint: disable=protobuf-undefined-attribute
import json

import pytest
from google.protobuf.message import Message

from zigopt.protobuf.dict import dict_to_protobuf, protobuf_to_dict
from zigopt.protobuf.gen.test.message_pb2 import Child, Parent
from zigopt.protobuf.lib import copy_protobuf, get_oneof_value


def test_copy_from():
  reference_value = Parent()
  set_reference_values(reference_value)
  assert_reference_values((reference_value))

  p = Parent()
  p.CopyFrom(reference_value)
  assert_reference_values((p))

  p = Parent()
  p.MergeFrom(reference_value)
  assert_reference_values((p))


def assert_all_fields_unset(immutable):
  for field in [
    "optional_double_field",
    "optional_string_field",
    "optional_composite_field",
    "optional_recursive_field",
  ]:
    assert not immutable.HasField(field)


def set_reference_values(builder):
  builder.optional_double_field = 1.0
  builder.optional_string_field = "test"
  builder.optional_composite_field.name = "name1"
  builder.optional_composite_field.value = 2.0
  builder.optional_composite_field.recursive.name = "name2"
  builder.optional_recursive_field.optional_recursive_field.optional_double_field = 5.0
  builder.repeated_double_field.extend([11.0, 12.0])
  builder.repeated_string_field.extend(["abc", "def"])
  first = builder.repeated_composite_field.add()
  first.name = "name3"
  first.value = 5.0
  second = builder.repeated_composite_field.add()
  second.recursive.name = "name4"
  builder.repeated_recursive_field.extend([Parent()])
  return builder


def assert_reference_values(immutable):
  assert_eq(immutable.optional_double_field, 1.0)
  assert_eq(immutable.optional_string_field, "test")

  assert_eq(immutable.optional_composite_field.name, "name1")
  assert_eq(immutable.optional_composite_field.value, 2.0)
  assert_eq(immutable.optional_composite_field.recursive.name, "name2")

  assert_eq(
    immutable.optional_composite_field,
    (Child(name="name1", value=2.0, recursive=Child(name="name2"))),
  )

  assert_eq(immutable.optional_recursive_field.optional_recursive_field.optional_double_field, 5.0)
  assert_eq(
    immutable.optional_recursive_field.optional_recursive_field,
    (Parent(optional_double_field=5.0)),
  )


def test_copy_protobuf():
  empty = Parent()
  assert_all_fields_unset(empty)
  ref = Parent()
  set_reference_values(ref)
  assert_reference_values((ref))
  ref2 = copy_protobuf(ref)
  assert_reference_values(((ref2)))
  assert_eq((ref), ((ref2)))
  ref2.repeated_string_field.append("abc")
  assert ref2 != copy_protobuf(ref)
  assert (ref2) != ref
  assert copy_protobuf(ref) != ref2
  assert ref != (ref2)

  empty = Parent()
  mutable_empty_1 = copy_protobuf(empty)
  mutable_empty_2 = copy_protobuf(empty)
  assert_eq((mutable_empty_1), empty)
  assert_eq((mutable_empty_2), empty)
  assert mutable_empty_1 == mutable_empty_2
  assert_eq((mutable_empty_1), (mutable_empty_2))

  mutable_empty_1.optional_string_field = "test"
  assert_eq((mutable_empty_2), empty)
  assert (mutable_empty_1) != empty
  assert mutable_empty_1 != mutable_empty_2

  mutable_empty_2.optional_string_field = "test"
  assert mutable_empty_1 == mutable_empty_2
  assert_eq((mutable_empty_1), (mutable_empty_2))
  assert mutable_empty_1 != empty
  assert mutable_empty_2 != empty


def test_to_dict():
  empty = Parent()
  reference = Parent()
  set_reference_values(reference)

  assert protobuf_to_dict(empty) == {}
  assert_eq((dict_to_protobuf(Parent, {})), empty)

  assert_eq(empty, (dict_to_protobuf(Parent, protobuf_to_dict(empty))))
  assert_eq(reference, (dict_to_protobuf(Parent, protobuf_to_dict(reference))))

  nonstandard_serialization = Parent()
  nonstandard_serialization.variable_name = "abc"
  assert_eq(protobuf_to_dict(nonstandard_serialization), {"serialized_name": "abc"})
  assert_eq(dict_to_protobuf(Parent, {"serialized_name": "abc"}), Parent(variable_name="abc"))


def test_large_floats():
  # Postgres stores numbers as the postgres `numeric` type which has higher precision
  # than the 64-bit floating points that we use in protobufs. Hence, some large ints
  # can end up stored in the DB, and then when deserialized they come back as longs.
  # To ensure consistency, we should always convert floats to floats
  number_too_big_for_precise_int = 1000000000000000000000000
  assert number_too_big_for_precise_int != float(number_too_big_for_precise_int)
  j = json.loads(f'{{"optional_double_field": {number_too_big_for_precise_int}}}')
  assert isinstance(dict_to_protobuf(Parent, j).optional_double_field, float)
  assert dict_to_protobuf(Parent, j).optional_double_field == float(number_too_big_for_precise_int)


def test_setattr():
  # pylint: disable=assigning-non-slot,protobuf-type-error
  empty = Parent()
  assert not empty.HasField("optional_double_field")
  assert not empty.optional_composite_field.HasField("name")
  with pytest.raises(TypeError):
    empty.optional_double_field = None  # type: ignore
  with pytest.raises(TypeError):
    empty.optional_composite_field.name = None  # type: ignore
  assert not empty.HasField("optional_double_field")
  assert not empty.optional_composite_field.HasField("name")
  empty.optional_double_field = 1.0
  empty.optional_composite_field.name = "abc"
  assert empty.HasField("optional_double_field")
  assert empty.optional_double_field == 1.0
  assert empty.optional_composite_field.HasField("name")
  assert empty.optional_composite_field.name == "abc"

  with pytest.raises(AttributeError):
    empty.fake_field = 1  # type: ignore
  with pytest.raises(AttributeError):
    empty.fake_field = None  # type: ignore


def test_get_oneof_value():
  # pylint: disable=pointless-statement
  message = Parent()
  with pytest.raises(TypeError):
    get_oneof_value(message, "oneof_value")

  message.oneof_double_field = 1.0
  assert get_oneof_value(message, "oneof_value") == message.oneof_double_field == 1.0
  message.oneof_string_field = "abc"
  assert get_oneof_value(message, "oneof_value") == message.oneof_string_field == "abc"
  message.oneof_composite_field.value = 1.0
  assert get_oneof_value(message, "oneof_value") == message.oneof_composite_field == Child(value=1.0)

  message.ClearField("oneof_value")
  with pytest.raises(TypeError):
    assert get_oneof_value(message, "oneof_value")

  with pytest.raises(ValueError):
    get_oneof_value(Parent(), "optional_double_field")

  with pytest.raises(ValueError):
    get_oneof_value(Parent(), "optional_recursive_field")

  with pytest.raises(ValueError):
    get_oneof_value(Parent(), "map_field")

  for message in (Parent(), Parent(oneof_double_field=1.0)):
    with pytest.raises(AttributeError):
      message.oneof_value  # type: ignore


def assert_eq(v1, v2):
  assert v1 == v2
  assert v2 == v1
  if isinstance(v1, Message):
    assert v1.SerializeToString() == v2.SerializeToString()
  assert (v1 != v2) is False
  assert (v2 != v1) is False
