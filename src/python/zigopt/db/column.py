# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json

import google.protobuf
import google.protobuf.descriptor
import google.protobuf.json_format
import sqlalchemy
import sqlalchemy.dialects.postgresql.json as json_operators
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import default_comparator, operators
from sqlalchemy.sql.elements import ClauseElement
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.sql.functions import coalesce as sql_coalesce
from sqlalchemy.types import DateTime, TypeDecorator

from zigopt.common import *
from zigopt.common.sigopt_datetime import aware_datetime_to_naive_datetime, naive_datetime_to_aware_datetime
from zigopt.protobuf.dict import protobuf_to_dict
from zigopt.protobuf.json import emit_json_with_descriptor, get_json_key, parse_json_with_descriptor
from zigopt.protobuf.lib import copy_protobuf, is_protobuf


def recursive_copy_protobuf(v):
  if is_sequence(v):
    return [recursive_copy_protobuf(t) for t in v]
  if is_mapping(v):
    return map_dict(recursive_copy_protobuf, dict(v))
  if is_protobuf(v):
    return copy_protobuf(v)
  return v


# TODO(SN-1076): This may need to be turned into an actual FunctionElement,
# need to figure out string escaping though
def JsonPath(*args):
  return "{" + ",".join(json.dumps(a) for a in args) + "}"


# Given a sqlalchemy expression of the form ExperimentMeta['a'][0]['c'],
# returns ['a', 0, 'c']
def unwind_json_path(json_path_expression):
  expression_children = json_path_expression.get_children()
  if not expression_children:
    return []
  parent = expression_children[0]
  path_clause = expression_children[1]
  if isinstance(path_clause, sqlalchemy.sql.elements.Cast):
    path_clause = path_clause.clause
  path_value = path_clause.value
  return unwind_json_path(parent) + [path_value]


def _object_to_json(value):
  if is_protobuf(value):
    return protobuf_to_dict(value)
  if is_mapping(value):
    return {k: _object_to_json(v) for k, v in value.items()}
  if is_sequence(value):
    return [_object_to_json(v) for v in value]
  return value


def adapt_for_jsonb(value):
  value = _object_to_json(value)
  if isinstance(value, ClauseElement):
    return value
  return json.dumps(value, separators=(",", ":"))


class jsonb_strip_nulls(GenericFunction):
  name = "jsonb_strip_nulls"
  type = JSONB


class jsonb_set(FunctionElement):
  name = "jsonb_set"

  def __init__(self, *args):
    if not 3 <= len(args) <= 4:
      raise ValueError(f"jsonb_set takes either 3 or 4 arguments, {len(args)} given")
    super().__init__(*args)


class jsonb_array_length(GenericFunction):
  name = "jsonb_array_length"
  type = sqlalchemy.Integer


@compiles(jsonb_set)
def compile_jsonb_set(element, compiler, **kw):
  args = list(element.clauses)
  if isinstance(args[2], sqlalchemy.sql.elements.BindParameter):
    args[2] = sqlalchemy.bindparam(args[2].key, value=adapt_for_jsonb(args[2].value))
  compiled_args = [compiler.process(arg) for arg in args]
  if isinstance(args[2], sqlalchemy.sql.elements.Null):
    compiled_args[2] = "'null'::jsonb"
  elif isinstance(args[2], sqlalchemy.sql.elements.BindParameter) and is_string(args[2].value):
    compiled_args[2] = f"{compiled_args[2]}::jsonb"
  else:
    compiled_args[2] = f"coalesce(to_jsonb({compiled_args[2]}),'null')"
  concatted = ",".join(compiled_args)
  return f"jsonb_set({concatted})"


def _raise_for_is_usage():
  raise NotImplementedError(
    "is_/isnot may not behave as expected with ProtobufColumns due to default values."
    " Prefer HasField which should return values consistent with native protobufs."
  )


def extend_with_forbid_is_clause(Cls: type):
  class Subclass(Cls):
    class comparator_factory(Cls.comparator_factory):  # type: ignore
      def is_(self, arg):
        _raise_for_is_usage()

      def isnot(self, arg):
        _raise_for_is_usage()

  Subclass.__name__ = Cls.__name__ + "_ForbidIsClause"
  return Subclass


def _default_value_for_descriptor(message_factory, descriptor):
  if isinstance(descriptor, google.protobuf.descriptor.Descriptor):
    Cls = message_factory.GetPrototype(descriptor)
    return Cls()
  if isinstance(descriptor, google.protobuf.descriptor.FieldDescriptor):
    if descriptor.label == google.protobuf.descriptor.FieldDescriptor.LABEL_REPEATED:
      # pylint: disable=protected-access
      if google.protobuf.json_format._IsMapEntry(descriptor):  # type: ignore
        return {}
      # pylint: enable=protected-access
      return []
    return descriptor.default_value
  return descriptor()


class _ProtobufColumnType(TypeDecorator):
  impl = JSONB

  def __init__(self, descriptor, message_factory, proxy=None, with_default=True):
    self._descriptor = descriptor
    self._proxy = proxy
    self._message_factory = message_factory
    self._with_default = with_default
    super().__init__(none_as_null=True)

  def __repr__(self):
    descriptor_name = getattr(self._descriptor, "full_name", getattr(self._descriptor, "__name__", self._descriptor))
    return (
      f"{self.__class__.__name__}(descriptor={descriptor_name}, proxy={self._proxy}, with_default={self._with_default})"
    )

  def process_bind_param(self, value, dialect):
    if value is None:
      return None
    return emit_json_with_descriptor(recursive_copy_protobuf(value), self._descriptor)

  def process_result_value(self, value, dialect):
    if value is None:
      result = _default_value_for_descriptor(self._message_factory, self._descriptor)
    else:
      result = parse_json_with_descriptor(
        value,
        self._descriptor,
        self._message_factory,
        ignore_unknown_fields=True,
      )
    if self._proxy:
      result = self._proxy(result)
    return result

  def process_literal_param(self, value, dialect):
    if value is None:
      return None
    return self.process_result_value(value, dialect)

  def copy(self, **kw):
    return _ProtobufColumnType(self._descriptor, self._message_factory, self._proxy, self._with_default)

  # pylint: disable=invalid-overridden-method
  def comparator_factory(self, *args, **kwargs):
    (expr,) = args
    type_ = expr.type
    if isinstance(type_, JSONB) and not isinstance(type_, _ProtobufColumnType):
      return super().comparator_factory(*args, **kwargs)
    return _ProtobufColumnType.Comparator(self._descriptor, self._message_factory, self._with_default, *args, **kwargs)

  # pylint: enable=invalid-overridden-method

  class Comparator(JSONB.Comparator):
    def __init__(self, descriptor, message_factory, with_default, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self._descriptor = descriptor
      self._message_factory = message_factory
      self._with_default = with_default

    @classmethod
    def _is_terminal_descriptor(cls, descriptor):
      # Returns true if this descriptor is the last descriptor in a protobuf chain -
      # i.e. refers to a scalar field (and hence is just a callable like `str`, `float`, etc.)
      return hasattr(descriptor, "__call__")

    def _maybe_with_default(self, clause):
      if not self._is_terminal_descriptor(self._descriptor):
        raise Exception(
          "Invalid descriptor for default values - it is likely you are trying to cast repeated/composite field"
        )
      default_value = _default_value_for_descriptor(self._message_factory, self._descriptor)
      return sql_coalesce(clause, default_value) if self._with_default else clause

    @property
    def astext(self):
      raise NotImplementedError(
        "Do not call `astext` on ProtobufColumns - prefer `as_string()` if you want a string value."
      )

    @property
    def real_astext(self):
      return super().astext

    # TODO(SN-1077): It might be possible to remove these casts in the future by inferring
    # the types from the protobuf record...
    def as_string(self):
      return self._maybe_with_default(self.real_astext.cast(extend_with_forbid_is_clause(sqlalchemy.types.Text)))

    def as_boolean(self):
      return self._maybe_with_default(self.real_astext.cast(extend_with_forbid_is_clause(sqlalchemy.types.Boolean)))

    def as_numeric(self):
      return self._maybe_with_default(self.real_astext.cast(extend_with_forbid_is_clause(sqlalchemy.types.Numeric)))

    def as_integer(self):
      return self._maybe_with_default(self.real_astext.cast(extend_with_forbid_is_clause(sqlalchemy.types.Integer)))

    def operate(self, operator, *other, **kwargs):
      OPERATORS_REQUIRING_DEFAULTS = (
        json_operators.ASTEXT,
        json_operators.JSONPATH_ASTEXT,
        operators.eq,
        operators.ne,
        operators.concat_op,
      )
      OPERATORS_FORBIDDING_DEFAULTS = (
        operators.is_,
        operators.isnot,
        operators.json_getitem_op,
        operators.json_path_getitem_op,
      )
      OPERATORS_REQUIRING_CAST = (
        operators.add,
        operators.ge,
        operators.gt,
        operators.ilike_op,
        operators.le,
        operators.like_op,
        operators.lt,
        operators.mul,
        operators.sub,
        operators.truediv,
      )
      operator_name = operator.opstring if hasattr(operator, "opstring") else repr(operator)
      if operator in OPERATORS_REQUIRING_DEFAULTS:
        default_value = _default_value_for_descriptor(self._message_factory, self._descriptor)
        with_default = sql_coalesce(self.expr, adapt_for_jsonb(default_value))
        # NOTE: This implementation is taken from `operate` in `sqlalchemy.sql.type_api`
        o = default_comparator.operator_lookup[operator.__name__]
        return o[0](with_default, operator, *(other + o[1:]), **kwargs)
      if operator in OPERATORS_REQUIRING_CAST:
        raise ValueError(
          f"It is unsafe to compare fields with {operator_name} - cast values using `as_X` before comparing."
        )
      if operator not in OPERATORS_FORBIDDING_DEFAULTS:
        # TODO(SN-1078): These lists can certainly be expanded with new operators, but it is dangerous to apply or not
        # apply defaults without knowing what the operator is. So throw a NotImplementedError unless we know about the
        # operator. If you are adding a new operator here, think about whether it makes sense for the protobuf default
        # value to be used instead of NULL when the value is missing. If it is appropriate to make that replacement,
        # the operator should be in OPERATORS_REQUIRING_DEFAULTS, otherwise OPERATORS_FORBIDDING_DEFAULTS
        raise NotImplementedError(f"Unsupported operator: {operator_name}")
      return super().operate(operator, *other, **kwargs)

    def _real_getitem(self, key, with_default):
      operator, right_expr, _ = self._setup_getitem(key)  # pylint: disable=no-value-for-parameter
      try:
        if self._is_terminal_descriptor(self._descriptor):
          raise KeyError(key)
        next_cls = get_json_key(self._descriptor, key, json=True)
      except ValueError as e:
        raise KeyError(key) from e
      next_type = _ProtobufColumnType(next_cls, self._message_factory, with_default=with_default)
      return self.operate(operator, right_expr, result_type=next_type)

    def _get_field_descriptor(self, key):
      return self._descriptor.fields_by_name[key]

    def _get_value_from_descriptor(self, key, with_default):
      try:
        field_descriptor = self._get_field_descriptor(key)
      except KeyError as e:
        raise AttributeError(f"Invalid descriptor attribute: {key}") from e
      json_name = field_descriptor.json_name
      return self._real_getitem(json_name, with_default=with_default)

    def HasField(self, key):
      return self._get_value_from_descriptor(key, with_default=False).real_isnot(None)

    def is_(self, other):
      _raise_for_is_usage()

    def isnot(self, other):
      _raise_for_is_usage()

    def real_isnot(self, arg):
      return JSONB.Comparator.isnot(self, arg)

    def __getitem__(self, key):
      if is_integer(key) or (
        isinstance(self._descriptor, google.protobuf.descriptor.FieldDescriptor)
        and
        # pylint: disable=protected-access
        google.protobuf.json_format._IsMapEntry(self._descriptor)  # type: ignore
        # pylint: enable=protected-access
      ):
        return self._real_getitem(key, with_default=True)
      # Fallback to regular JSONB
      operator, right_expr, _ = self._setup_getitem(key)  # pylint: disable=no-value-for-parameter
      return self.operate(operator, right_expr, result_type=JSONB)

    def __getattr__(self, name):
      return self._get_value_from_descriptor(name, with_default=True)


class ImpliedUTCDateTime(TypeDecorator):
  impl = DateTime

  def process_bind_param(self, value, dialect):
    if value is None:
      return None
    return aware_datetime_to_naive_datetime(value)

  def process_result_value(self, value, dialect):
    if value is None:
      return None
    return naive_datetime_to_aware_datetime(value)

  def process_literal_param(self, value, dialect):
    return self.process_bind_param(value, dialect)


class ProtobufColumn(sqlalchemy.Column):
  """
    ProtobufColumn is intended to make protobuf objects that are stored as JSONB
    blobs queryable inside SQL by extending the protobuf API to SQL operations. The goal
    is to make these operations behave identically whether the operation is carried out
    through a SQL operation or on a protobuf object. Supported operations include:

      - field acceses (including returning default values for unset fields)
      - HasField
    """

  _constructor = sqlalchemy.Column

  def __init__(self, cls, proxy=None, **kwargs):
    message_factory = google.protobuf.symbol_database.Default()  # type: ignore
    super().__init__(type_=_ProtobufColumnType(cls.DESCRIPTOR, message_factory, proxy=proxy), **kwargs)
    self._cls = cls
    self._proxy = proxy

  @property
  def protobuf_class(self):
    return self._cls

  def default_value(self):
    ret = self._cls()
    if self._proxy:
      ret = self._proxy(ret)
    return ret


# NOTE: This still needs to be specified manually. It would be
# awesome if this was applied automatically to every ProtobufColumn,
# but AFAICT that would require an update to sqlalchemy
def ProtobufColumnValidator(meta, proxy=None):
  if meta is None:
    return None
  r = meta
  if proxy:
    r = proxy(r)
  return r
