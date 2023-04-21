# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# pylint: disable=use-implicit-booleaness-not-comparison
import numpy
import pytest

from zigopt.common import *
from zigopt.protobuf.gen.test.message_pb2 import Parent


class TestLists:
  # pylint: disable=too-many-public-methods
  @pytest.mark.parametrize(
    "input_list,expected",
    [
      ([], []),
      ([[]], []),
      ([[1]], [1]),
      ([[1, 3]], [1, 3]),
      ([[1, 3], [], [], [2]], [1, 3, 2]),
      ([[1, 3], [], [], [2, [4]]], [1, 3, 2, [4]]),
      (([i] for i in range(5)), list(range(5))),
    ],
  )
  def test_flatten(self, input_list, expected):
    assert flatten(input_list) == expected

  def test_tail(self):
    assert tail([], 0) == []
    assert tail([], 1) == []
    assert tail([], 5) == []
    assert tail([1], 5) == [1]
    assert tail([None], 5) == [None]
    assert tail([1, 2, 3, 4, 5], 5) == [1, 2, 3, 4, 5]
    assert tail([1, 2, 3, 4, 5], 3) == [3, 4, 5]
    assert tail([1, 2, 3, 4, 5], 0) == []
    assert tail([1, 2, 3, 4, 5], -2) == []

    with pytest.raises(Exception):
      tail([], None)
    with pytest.raises(Exception):
      tail([1, 2, 3], None)

  @pytest.mark.parametrize(
    "input_data,expected",
    [
      ((), []),
      ((False, None, [], 0, {}), []),
      ((False, None, [], 0, {}, 1, 2, 3, True, [1]), [1, 2, 3, True, [1]]),
      ([], []),
      ([False, None, [], 0, {}], []),
      ([False, None, [], 0, {}, 1, 2, 3, True, [1]], [1, 2, 3, True, [1]]),
    ],
  )
  def test_compact_sequence(self, input_data, expected):
    assert compact_sequence(input_data) == expected

  @pytest.mark.parametrize(
    "input_data,expected",
    [
      ({}, {}),
      (
        {
          "a": False,
          "b": None,
          "c": [],
          "d": 0,
          "e": {},
        },
        {},
      ),
      (
        {"a": False, "b": None, "c": [], "d": 0, "e": {}, "f": 1, "g": True},
        {
          "f": 1,
          "g": True,
        },
      ),
      (
        {"a": {"b": None}},
        {
          "a": {
            "b": None,
          },
        },
      ),
    ],
  )
  def test_compact_mapping(self, input_data, expected):
    assert compact_mapping(input_data) == expected

  def test_remove_nones(self):
    assert remove_nones(()) == ()
    assert remove_nones((False, None, [], 0, {})) == (False, [], 0, {})
    assert remove_nones((False, None, [], 0, {}, 1, 2, 3, True, [1])) == (False, [], 0, {}, 1, 2, 3, True, [1])

    assert remove_nones([]) == []
    assert remove_nones([False, None, [], 0, {}]) == [False, [], 0, {}]
    assert remove_nones([False, None, [], 0, {}, 1, 2, 3, True, [1]]) == [False, [], 0, {}, 1, 2, 3, True, [1]]
    assert remove_nones({}) == {}
    assert remove_nones({"a": False, "b": None, "c": [], "d": 0, "e": {}}) == {
      "a": False,
      "c": [],
      "d": 0,
      "e": {},
    }
    assert remove_nones({"a": False, "b": None, "c": [], "d": 0, "e": {}, "f": 1, "g": True}) == {
      "a": False,
      "c": [],
      "d": 0,
      "e": {},
      "f": 1,
      "g": True,
    }
    assert remove_nones({"a": {"b": None}}) == {
      "a": {
        "b": None,
      },
    }
    assert remove_nones(set((1, "a", None))) == set((1, "a"))
    assert remove_nones(set((1, "a"))) == set((1, "a"))
    assert remove_nones(set()) == set()

    with pytest.raises(ValueError):
      remove_nones(None)  # type: ignore

    with pytest.raises(ValueError):
      remove_nones(1)  # type: ignore

    with pytest.raises(ValueError):
      remove_nones("abc")  # type: ignore

    with pytest.raises(ValueError):
      remove_nones(b"abc")  # type: ignore

    with pytest.raises(ValueError):
      remove_nones(numpy.array([]))  # type: ignore

  def test_coalesce(self):
    assert coalesce() is None
    assert coalesce(None) is None
    assert coalesce(None, None) is None
    assert coalesce(None, None, None) is None
    assert coalesce(True) is True
    assert coalesce(False) is False
    assert coalesce(None, 1) == 1
    assert coalesce(None, 0) == 0
    assert coalesce(None, 0, 5) == 0
    assert coalesce(None, 1, 5) == 1

  def test_distinct_counts(self):
    assert distinct_counts([]) == {}
    assert distinct_counts([1, 2]) == {1: 1, 2: 1}
    assert distinct_counts([1, 1, 2]) == {1: 2, 2: 1}
    assert distinct_counts((i for i in range(3))) == {0: 1, 1: 1, 2: 1}

  def test_partition(self):
    assert partition([], lambda x: True) == ([], [])
    assert partition([], lambda x: False) == ([], [])
    assert partition([1, 2], lambda x: True) == ([1, 2], [])
    assert partition([1, 2], lambda x: False) == ([], [1, 2])
    assert partition([1, 2, 3, 4], lambda x: x % 2 == 0) == ([2, 4], [1, 3])
    assert partition((i for i in range(1, 5)), lambda x: x % 2 == 0) == ([2, 4], [1, 3])

  def test_distinct(self):
    assert distinct([]) == []
    assert distinct([1]) == [1]
    assert distinct([1, 2]) == [1, 2]
    assert distinct([1, 1, 2]) == [1, 2]
    assert distinct([1, 2, 2]) == [1, 2]
    assert distinct([2, 1, 1]) == [2, 1]
    assert distinct(list(i for i in range(5))) == list(range(5))

    assert distinct(()) == ()
    assert distinct((1, 2)) == (1, 2)
    assert distinct((1, 1, 2)) == (1, 2)

    with pytest.raises(ValueError):
      distinct({})  # type: ignore

    with pytest.raises(ValueError):
      distinct(set([]))  # type: ignore

    with pytest.raises(ValueError):
      distinct("abc")  # type: ignore

    with pytest.raises(ValueError):
      distinct(None)  # type: ignore

  def test_distinct_by(self):
    assert distinct_by((), key=lambda x: x) == ()  # type: ignore
    assert distinct_by((1, 2), key=lambda x: x) == (1, 2)
    assert distinct_by((1, 1, 2), key=lambda x: x) == (1, 2)

    assert distinct_by([], key=lambda x: x) == []
    assert distinct_by([1], key=lambda x: x) == [1]
    assert distinct_by([1, 2], key=lambda x: x) == [1, 2]
    assert distinct_by([1, 1, 2], key=lambda x: x) == [1, 2]
    assert distinct_by([1, 2, 2], key=lambda x: x) == [1, 2]
    assert distinct_by([2, 1, 1], key=lambda x: x) == [2, 1]

    assert distinct_by([], key=lambda x: x % 2) == []
    assert distinct_by([1], key=lambda x: x % 2) == [1]
    assert distinct_by([1, 2], key=lambda x: x % 2) == [1, 2]
    assert distinct_by([1, 1, 2], key=lambda x: x % 2) == [1, 2]
    assert distinct_by([1, 2, 2], key=lambda x: x % 2) == [1, 2]
    assert distinct_by([2, 1, 1], key=lambda x: x % 2) == [2, 1]
    assert distinct_by([1, 2, 3, 4], key=lambda x: x % 2) == [1, 2]
    assert distinct_by([1, 3, 2], key=lambda x: x % 2) == [1, 2]
    assert distinct_by([1, 2, 4], key=lambda x: x % 2) == [1, 2]
    assert distinct_by([2, 1, 3], key=lambda x: x % 2) == [2, 1]

  def test_find(self):
    assert find([], lambda x: True) is None
    assert find([1], lambda x: True) == 1
    assert find([1], lambda x: False) is None
    assert find([1, 2], lambda x: True) == 1
    assert find([1, 2], lambda x: x % 2 == 0) == 2
    assert find([1, 2, 4, 6], lambda x: x % 2 == 0) == 2
    assert find((i for i in range(1, 5)), lambda x: x % 2 == 0) == 2

  def test_as_grouped_dict(self):
    assert as_grouped_dict([], lambda x: x) == {}  # type: ignore
    assert as_grouped_dict([1], lambda x: x) == {1: [1]}
    assert as_grouped_dict([1, 2], lambda x: x) == {1: [1], 2: [2]}
    assert as_grouped_dict([1, 2], lambda x: x % 2) == {1: [1], 0: [2]}
    assert as_grouped_dict([1, 2, 3, 4], lambda x: x % 2) == {1: [1, 3], 0: [2, 4]}
    assert as_grouped_dict((i for i in range(1, 5)), lambda x: x % 2) == {1: [1, 3], 0: [2, 4]}

  def test_to_map_by_key(self):
    assert to_map_by_key([], lambda x: x) == {}  # type: ignore
    assert to_map_by_key([1], lambda x: x) == {1: 1}
    assert to_map_by_key([1, 2], lambda x: x) == {1: 1, 2: 2}
    assert to_map_by_key([1, 2], lambda x: x % 2) == {1: 1, 0: 2}
    assert to_map_by_key([1, 2, 3, 4], lambda x: x % 2) == {1: 3, 0: 4}
    assert to_map_by_key((i for i in range(1, 5)), lambda x: x % 2) == {1: 3, 0: 4}

  def test_map_dict(self):
    assert map_dict(lambda x: x, {}) == {}  # type: ignore
    assert map_dict(lambda x: x * 2, {}) == {}
    assert map_dict(lambda x: x * 2, {"a": 1}) == {"a": 2}

    b = {"a": 1}
    assert map_dict(lambda x: x, b) == b
    assert id(map_dict(lambda x: x, b)) != b

    c = {"b": b}
    assert map_dict(lambda x: 1, c) == {"b": 1}
    assert map_dict(lambda x: x, c) == c
    assert id(map_dict(lambda x: x, c)) != c

    d = {"l": [1, 2, 3]}
    assert map_dict(lambda x: 1, d) == {"l": 1}

    e = {"o": [{"r": 2}]}
    assert map_dict(lambda x: 1, e) == {"o": 1}

  def test_recursively_map_dict(self):
    assert recursively_map_dict(lambda x: x, {}) == {}
    assert recursively_map_dict(lambda x: x * 2, {}) == {}
    assert recursively_map_dict(lambda x: x * 2, {"a": 1}) == {"a": 2}

    b = {"a": 1}
    assert recursively_map_dict(lambda x: x, b) == b
    assert id(recursively_map_dict(lambda x: x, b)) != b

    c = {"b": b}
    assert recursively_map_dict(lambda x: 1, c) == {"b": {"a": 1}}
    assert recursively_map_dict(lambda x: x, c) == c
    assert id(recursively_map_dict(lambda x: x, c)) != c

    d = {"l": [1, 2, 3]}
    assert recursively_map_dict(lambda x: 1, d) == {"l": [1, 1, 1]}

    e = {"o": [{"r": 2}]}
    assert recursively_map_dict(lambda x: 1, e) == {"o": [{"r": 1}]}

  def test_filter_keys(self):
    assert filter_keys(lambda k: bool(1 / 0), {}) == {}
    assert filter_keys(lambda k: k == "y", {"h": 4, "y": 2}) == {"y": 2}
    assert filter_keys(lambda k: k.startswith("h"), {"hello": 1, "goodbye": 2}) == {"hello": 1}

  def test_recursively_filter_keys(self):
    assert recursively_filter_keys(lambda k: k, []) == []
    assert recursively_filter_keys(lambda k: k, {}) == {}
    assert recursively_filter_keys(lambda k: k, [{}, [], [{}]]) == [{}, [], [{}]]
    assert recursively_filter_keys(lambda x: bool(len(x)), [{"a": 2}, {"": 3}, {}]) == [{"a": 2}, {}, {}]
    assert recursively_filter_keys(lambda x: bool(len(x)), [{"": 1, "a": 2}, {"": 3}, {}]) == [{"a": 2}, {}, {}]
    assert recursively_filter_keys(lambda k: k, [{True: 1, False: {True: 1}}, {True: {True: [{False: 3}]}}]) == [
      {True: 1},
      {True: {True: [{}]}},
    ]

  def test_recursively_omit_keys(self):
    assert recursively_omit_keys([], ["a"]) == []
    assert recursively_omit_keys({}, ["a"]) == {}
    assert recursively_omit_keys([{}, [], [{}]], ["a"]) == [{}, [], [{}]]
    assert recursively_omit_keys([{"a": 2}, {"o": 3}, {}], ["o"]) == [{"a": 2}, {}, {}]
    assert recursively_omit_keys([{"a": 2}, {"o": 3}, {}], ["a", "o"]) == [{}, {}, {}]
    assert recursively_omit_keys([{"o": 1, "a": 2}, {"o": 3}, {"a": [{"o": 4}]}], ["o"]) == [{"a": 2}, {}, {"a": [{}]}]

  def test_extend_dict(self):
    assert extend_dict({}) == {}
    assert extend_dict({}, {}) == {}
    assert extend_dict({}, {}, {}) == {}

    assert extend_dict({"a": 1, "b": 2}) == {"a": 1, "b": 2}
    assert extend_dict({}, {"a": 1, "b": 2}) == {"a": 1, "b": 2}  # type: ignore
    assert extend_dict({"a": 1, "b": 2}, {"a": 3, "c": 4}) == {"a": 3, "b": 2, "c": 4}
    assert extend_dict({}, {"a": 1, "b": 2}, {"a": 3, "c": 4}) == {"a": 3, "b": 2, "c": 4}  # type: ignore

    a = {"d": 1}
    extend_dict(a, {"e": 2})
    assert a["d"] == 1
    assert a["e"] == 2
    extend_dict({}, a, {"e": 3})  # type: ignore
    assert a["e"] == 2

    with pytest.raises(AssertionError):
      extend_dict(1, 1)  # type: ignore

    with pytest.raises(AssertionError):
      extend_dict([], [])  # type: ignore

    with pytest.raises(AssertionError):
      extend_dict(set([]), set([]))  # type: ignore

  def test_invert_dict(self):
    assert invert_dict({}) == {}
    assert invert_dict({"a": 1}) == {1: "a"}
    assert invert_dict({"a": 1, "b": 2}) == {1: "a", 2: "b"}

    d = {"a": 1, "b": 2}
    assert invert_dict(invert_dict(d)) == d

    with pytest.raises(AssertionError):
      invert_dict([])  # type: ignore

    with pytest.raises(ValueError):
      invert_dict({"a": 1, "b": 1})

  def test_max_option(self):
    assert max_option([]) is None
    assert min_option([]) is None
    assert max_option([1]) == 1
    assert min_option([1]) == 1
    assert max_option([1, 2, 3, 4]) == 4
    assert min_option([1, 2, 3, 4]) == 1

    assert max_option([], key=lambda x: x) is None
    assert min_option([], key=lambda x: x) is None
    assert max_option([1], key=lambda x: x) == 1
    assert min_option([1], key=lambda x: x) == 1
    assert max_option([1, 2, 3, 4], key=lambda x: x) == 4
    assert min_option([1, 2, 3, 4], key=lambda x: x) == 1
    assert max_option([1, 2, 3, 4], key=lambda x: -x) == 1
    assert min_option([1, 2, 3, 4], key=lambda x: -x) == 4
    assert max_option((i for i in range(1, 5)), key=lambda x: -x) == 1
    assert min_option((i for i in range(1, 5)), key=lambda x: -x) == 4

  def test_list_get(self):
    assert list_get([], 0) is None
    assert list_get([], 100) is None
    assert list_get([], -5) is None
    assert list_get([1], 0) == 1
    assert list_get([1], -1) == 1
    assert list_get([1], 100) is None
    assert list_get([1, 2, 3], 0) == 1
    assert list_get([1, 2, 3], 2) == 3
    assert list_get([1, 2, 3], -1) == 3
    assert list_get([1, 2, 3], -3) == 1
    assert list_get([1, 2, 3], 100) is None

  def test_chunked(self):
    with pytest.raises(Exception):
      chunked([], 0)

    with pytest.raises(Exception):
      chunked([1], 0)

    with pytest.raises(Exception):
      chunked([1, 2, 3, 4], 0)

    assert chunked([], 1) == []
    assert chunked([], 2) == []
    assert chunked([], 3) == []

    assert chunked([1], 1) == [(1,)]
    assert chunked([1], 2) == [(1, None)]
    assert chunked([1], 3) == [(1, None, None)]
    assert chunked([1], 1, fillvalue="x") == [(1,)]
    assert chunked([1], 2, fillvalue="x") == [(1, "x")]
    assert chunked([1], 3, fillvalue="x") == [(1, "x", "x")]

    assert chunked([1, 2], 1) == [(1,), (2,)]
    assert chunked([1, 2], 2) == [(1, 2)]
    assert chunked([1, 2], 3) == [(1, 2, None)]
    assert chunked([1, 2], 1, fillvalue="x") == [(1,), (2,)]
    assert chunked([1, 2], 2, fillvalue="x") == [(1, 2)]
    assert chunked([1, 2], 3, fillvalue="x") == [(1, 2, "x")]

    assert chunked([1, 2, 3], 1) == [(1,), (2,), (3,)]
    assert chunked([1, 2, 3], 2) == [(1, 2), (3, None)]
    assert chunked([1, 2, 3], 3) == [(1, 2, 3)]
    assert chunked([1, 2, 3], 4) == [(1, 2, 3, None)]
    assert chunked([1, 2, 3], 1000) == [(1, 2, 3) + (None,) * 997]

    assert chunked([1, 2, 3, 4, 5, 6], 4) == [(1, 2, 3, 4), (5, 6, None, None)]
    assert chunked((i for i in range(1, 7)), 4) == [(1, 2, 3, 4), (5, 6, None, None)]

  def test_sliding(self):
    with pytest.raises(Exception):
      sliding([], 0)

    with pytest.raises(Exception):
      sliding([1], 0)

    with pytest.raises(Exception):
      sliding([1, 2, 3, 4], 0)

    assert sliding([], 1) == []
    assert sliding([], 2) == []
    assert sliding([], 3) == []

    assert sliding([1], 1) == [(1,)]
    assert sliding([1], 2) == []
    assert sliding([1], 3) == []

    assert sliding([1, 2], 1) == [(1,), (2,)]
    assert sliding([1, 2], 2) == [(1, 2)]
    assert sliding([1, 2], 3) == []

    assert sliding([1, 2, 3], 1) == [(1,), (2,), (3,)]
    assert sliding([1, 2, 3], 2) == [(1, 2), (2, 3)]
    assert sliding([1, 2, 3], 3) == [(1, 2, 3)]
    assert sliding([1, 2, 3], 4) == []
    assert sliding([1, 2, 3], 1000) == []

    assert sliding([1, 2, 3, 4, 5, 6], 4) == [(1, 2, 3, 4), (2, 3, 4, 5), (3, 4, 5, 6)]
    assert sliding((i for i in range(1, 7)), 4) == [(1, 2, 3, 4), (2, 3, 4, 5), (3, 4, 5, 6)]

  def test_as_tuple(self):
    assert as_tuple(None) == (None,)
    assert as_tuple(True) == (True,)
    assert as_tuple(False) == (False,)
    assert as_tuple("abc") == ("abc",)
    assert as_tuple(0) == (0,)
    assert as_tuple(50) == (50,)
    assert as_tuple([1, 2, 3]) == (1, 2, 3)  # type: ignore
    assert as_tuple((1, 2, 3)) == (1, 2, 3)  # type: ignore
    assert as_tuple([1]) == (1,)  # type: ignore
    assert as_tuple((1,)) == (1,)  # type: ignore
    assert as_tuple([[[1]]]) == ([[1]],)  # type: ignore
    assert as_tuple(range(4)) == (0, 1, 2, 3)  # type: ignore
    assert as_tuple((i for i in range(4))) == (0, 1, 2, 3)  # type: ignore

  def test_omit(self):
    assert omit({}) == {}
    assert omit({}, "a") == {}  # type: ignore
    assert omit({}, "a", "b") == {}  # type: ignore
    assert omit({"a": 1}) == {"a": 1}
    assert omit({"a": 1}, "a") == {}
    assert omit({"a": 1}, "b") == {"a": 1}
    assert omit({"a": 1}, "a", "b") == {}
    assert omit({"a": 1, "c": "b"}, "a", "b") == {"c": "b"}

  def test_pick(self):
    assert pick({}) == {}
    assert pick({}, "a") == {}  # type: ignore
    assert pick({}, "a", "b") == {}  # type: ignore
    assert pick({"a": 1}) == {}
    assert pick({"a": 1}, "a") == {"a": 1}
    assert pick({"a": 1}, "b") == {}
    assert pick({"a": 1}, "a", "b") == {"a": 1}
    assert pick({"a": 1, "c": "b"}, "a", "b") == {"a": 1}

  def test_is_iterable(self):
    assert is_iterable([])
    assert is_iterable([1, 2, 3])
    assert is_iterable(())
    assert is_iterable((1, 2, 3))
    assert is_iterable(Parent().repeated_double_field)
    assert is_iterable(Parent().repeated_string_field)
    assert is_iterable(Parent().repeated_composite_field)
    assert is_iterable(Parent().repeated_recursive_field)
    assert is_iterable(Parent().map_field)
    assert is_iterable(numpy.array([]))
    assert is_iterable(numpy.array([1, 2, 3]))
    assert is_iterable(range(4))
    assert is_iterable({})
    assert is_iterable({"a": 123})
    assert is_iterable(set())
    assert is_iterable(set((1, "a")))
    assert is_iterable({1, "a"})
    assert is_iterable(frozenset((1, "a")))
    assert is_iterable((i for i in range(4)))

    assert not is_iterable(None)
    assert not is_iterable(False)
    assert not is_iterable(True)
    assert not is_iterable("abc")
    assert not is_iterable(b"abc")
    assert not is_iterable(0)
    assert not is_iterable(1.0)
    assert not is_iterable(Parent().optional_double_field)
    assert not is_iterable(Parent().optional_string_field)
    assert not is_iterable(Parent().optional_composite_field)
    assert not is_iterable(Parent().optional_recursive_field)

  def test_is_sequence(self):
    assert is_sequence([])
    assert is_sequence([1, 2, 3])
    assert is_sequence(())
    assert is_sequence((1, 2, 3))
    assert is_sequence(Parent().repeated_double_field)
    assert is_sequence(Parent().repeated_string_field)
    assert is_sequence(Parent().repeated_composite_field)
    assert is_sequence(Parent().repeated_recursive_field)
    assert is_sequence(numpy.array([]))
    assert is_sequence(numpy.array([1, 2, 3]))
    assert is_sequence(range(4))

    assert not is_sequence(None)
    assert not is_sequence(False)
    assert not is_sequence(True)
    assert not is_sequence(0)
    assert not is_sequence(1.0)
    assert not is_sequence("abc")
    assert not is_sequence(b"abc")
    assert not is_sequence({})
    assert not is_sequence({"a": 123})
    assert not is_sequence(Parent().optional_double_field)
    assert not is_sequence(Parent().optional_string_field)
    assert not is_sequence(Parent().optional_composite_field)
    assert not is_sequence(Parent().optional_recursive_field)
    assert not is_sequence(Parent().map_field)
    assert not is_sequence(set())
    assert not is_sequence(set((1, "a")))
    assert not is_sequence({1, "a"})
    assert not is_sequence(frozenset((1, "a")))
    assert not is_sequence((i for i in range(4)))

  def test_is_mapping(self):
    assert is_mapping({})
    assert is_mapping({"a": 123})
    assert is_mapping(Parent().map_field)

    assert not is_mapping([])
    assert not is_mapping([1, 2, 3])
    assert not is_mapping(())
    assert not is_mapping((1, 2, 3))
    assert not is_mapping(Parent().repeated_double_field)
    assert not is_mapping(Parent().repeated_string_field)
    assert not is_mapping(Parent().repeated_composite_field)
    assert not is_mapping(Parent().repeated_recursive_field)
    assert not is_mapping(numpy.array([]))
    assert not is_mapping(numpy.array([1, 2, 3]))
    assert not is_mapping(None)
    assert not is_mapping(False)
    assert not is_mapping(True)
    assert not is_mapping(0)
    assert not is_mapping(1.0)
    assert not is_mapping("abc")
    assert not is_mapping(Parent().optional_double_field)
    assert not is_mapping(Parent().optional_string_field)
    assert not is_mapping(Parent().optional_composite_field)
    assert not is_mapping(Parent().optional_recursive_field)
    assert not is_mapping(set())
    assert not is_mapping(set((1, "a")))
    assert not is_mapping({1, "a"})
    assert not is_mapping(frozenset((1, "a")))
    assert not is_mapping(range(4))
    assert not is_mapping((i for i in range(4)))

  def test_is_set(self):
    assert is_set(set())
    assert is_set(set((1, "a")))
    assert is_set({1, "a"})
    assert is_set(frozenset((1, "a")))

    assert not is_set({})
    assert not is_set({"a": 123})
    assert not is_set(Parent().map_field)
    assert not is_set([])
    assert not is_set([1, 2, 3])
    assert not is_set(())
    assert not is_set((1, 2, 3))
    assert not is_set(Parent().repeated_double_field)
    assert not is_set(Parent().repeated_string_field)
    assert not is_set(Parent().repeated_composite_field)
    assert not is_set(Parent().repeated_recursive_field)
    assert not is_set(numpy.array([]))
    assert not is_set(numpy.array([1, 2, 3]))
    assert not is_set(None)
    assert not is_set(False)
    assert not is_set(True)
    assert not is_set(0)
    assert not is_set(1.0)
    assert not is_set("abc")
    assert not is_set(Parent().optional_double_field)
    assert not is_set(Parent().optional_string_field)
    assert not is_set(Parent().optional_composite_field)
    assert not is_set(Parent().optional_recursive_field)
    assert not is_set(range(4))
    assert not is_set((i for i in range(4)))

  def test_safe_iterator(self):
    assert list(safe_iterator([])) == []
    assert list(safe_iterator([1, 2, 3])) == [1, 2, 3]
    assert list(safe_iterator(range(1, 4))) == [1, 2, 3]
    assert list(safe_iterator((i for i in range(1, 4)))) == [1, 2, 3]
    it = safe_iterator([1, 2, 3])
    assert next(it) == 1
    assert next(it) == 2
    assert next(it) == 3
    with pytest.raises(StopIteration):
      next(it)
    with pytest.raises(ValueError):
      next(it)

  def test_generator_to_list(self):
    @generator_to_list
    def gen():
      for i in range(4):
        yield i

    result = gen()
    assert is_iterable(result)
    assert result == [0, 1, 2, 3]

  def test_generator_to_safe_iterator(self):
    @generator_to_safe_iterator
    def gen():
      for i in range(4):
        yield i

    result = gen()
    assert is_iterable(result)
    assert isinstance(result, safe_iterator)
    assert list(result) == [0, 1, 2, 3]

  def test_generator_to_dict(self):
    @generator_to_dict
    def gen():
      for i in range(4):
        yield (str(i), i)

    result = gen()
    assert is_mapping(result)
    assert result == {"0": 0, "1": 1, "2": 2, "3": 3}
