# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Any, Callable, Optional, Sequence

from zigopt.common import *
from zigopt.common.lists import filter_keys, map_dict
from zigopt.handlers.validate.validate_dict import (
  IOValidatorInterface,
  TypeValidatorBase,
  ValidationType,
  validate_type,
)

from libsigopt.aux.errors import InvalidTypeError  # type: ignore


class JsonBuilderError(Exception):
  def __init__(self, msg: str, builder: "JsonBuilder"):
    super().__init__(msg)
    self.builder = builder


class MissingFieldError(JsonBuilderError):
  def __init__(self, builder: "JsonBuilder", field_name: str):
    super().__init__(
      f"missing field `{field_name}` in {type(builder).__name__}",
      builder,
    )
    self.field_name = field_name


class InvalidFieldError(JsonBuilderError):
  def __init__(self, builder: "JsonBuilder", field_name: str, type_error: TypeError):
    super().__init__(
      f"when resolving field `{field_name}` in {type(builder).__name__}: {str(type_error)}",
      builder,
    )
    self.field_name = field_name
    self.type_error = type_error


class BaseFieldResolver:
  def __init__(self, field_name: str, value_type: IOValidatorInterface):
    self.field_name = field_name
    self.value_type = value_type.get_output_validator()

  def entry(self) -> tuple[str, "BaseFieldResolver"]:
    return self.field_name, self

  def resolve(self, builder: "JsonBuilder") -> tuple[str, Any]:
    try:
      value = napply(self.get_value(builder), lambda result: validate_type(result, self.value_type))  # type: ignore
      return (self.field_name, value)
    except InvalidTypeError as e:
      raise InvalidFieldError(builder, self.field_name, e) from e

  def check(self, builder: "JsonBuilder") -> bool:
    raise NotImplementedError()

  def get_value(self, builder: "JsonBuilder") -> Any:
    raise NotImplementedError()


class FieldResolver(BaseFieldResolver):
  def __init__(
    self,
    func: Callable[[], Any],
    field_name: str,
    value_type: IOValidatorInterface,
    hide: Optional[Callable[[Any], bool]],
  ):
    super().__init__(field_name, value_type)
    self.func = func
    self.hide = hide

  def get_value(self, builder: "JsonBuilder") -> Any:
    return getattr(builder, self.func.__name__)()

  def check(self, builder: "JsonBuilder") -> bool:
    return self.hide is None or not self.hide(builder)


class ExposedFieldResolver(BaseFieldResolver):
  def __init__(self, exposer: "FieldExposer", field_name: str, value_type: IOValidatorInterface):
    super().__init__(field_name, value_type)
    self.exposer = exposer

  def get_value(self, builder: "JsonBuilder") -> Any:
    return self.exposer.get_field_value(builder, self.field_name)

  def check(self, builder: "JsonBuilder") -> bool:
    return True


class FieldExposer:
  def __init__(
    self,
    func: Callable[[], Any],
    fields: Sequence[tuple[str, IOValidatorInterface]],
    getter: Callable[[Any, str], Any],
  ):
    self.func = func
    self.fields = fields
    self.getter = getter

  def update_field_dict(self, field_dict: dict[str, BaseFieldResolver]) -> None:
    field_dict.update(
      ExposedFieldResolver(self, field_name, value_type).entry() for field_name, value_type in self.fields
    )

  def get_field_value(self, builder: "JsonBuilder", field_name: str) -> Any:
    return self.getter(getattr(builder, self.func.__name__)(), field_name)


def field(
  value_type: IOValidatorInterface,
  field_name: Optional[str] = None,
  hide: Optional[Callable[[Any], bool]] = None,
):
  def wrap_func(func, value_type=value_type, field_name=field_name, hide=hide):
    if hide is None:

      def hide(self):
        return False

    if field_name is None:
      field_name = func.__name__
    assert is_string(field_name)

    setattr(func, "__field_resolver", FieldResolver(func, field_name, value_type, hide))

    return func

  return wrap_func


def expose_fields(
  fields: Sequence[tuple[str, IOValidatorInterface]],
  getter: Callable[[object, str], Any] = lambda obj, attr: getattr(obj, attr, None),
):
  def wrap_func(func):
    setattr(func, "__field_exposer", FieldExposer(func=func, fields=fields, getter=getter))
    return func

  return wrap_func


class BuilderDetails:
  def __init__(self, object_type: str, field_dict: dict[str, BaseFieldResolver]):
    self.object_type = object_type
    self.field_dict = field_dict


class JsonBuilder:
  builder: BuilderDetails

  def __new__(cls, *args, **kwargs):
    instance = super().__new__(cls)
    field_dict = dict(
      getattr(func, "__field_resolver").entry()
      for func in (getattr(cls, attr) for attr in dir(cls))
      if hasattr(func, "__field_resolver")
    )
    for attr in dir(cls):
      func = getattr(cls, attr)
      field_exposer = getattr(func, "__field_exposer", False)
      if field_exposer:
        field_exposer.update_field_dict(field_dict)
    setattr(instance, "builder", BuilderDetails(cls.object_name, field_dict))
    return instance

  @classmethod
  def json(cls, *args, **kwargs) -> dict:
    return cls(*args, **kwargs).resolve_all()

  @field(ValidationType.string)
  def object(self) -> str:
    return self.builder.object_type

  def resolve_fields(self, fields: Optional[Sequence[str]] = None):
    field_dict = self.builder.field_dict

    def get_field(key: str) -> BaseFieldResolver:
      try:
        return field_dict[key]
      except KeyError as e:
        raise MissingFieldError(self, key) from e

    resolver_iter = field_dict.values() if fields is None else (get_field(f) for f in fields)

    return dict(resolver.resolve(self) for resolver in resolver_iter if resolver.check(self))

  def resolve_all(self) -> dict:
    return self.resolve_fields(fields=None)


class JsonBuilderValidationType(TypeValidatorBase):
  def __init__(self, *, builder_class: type[JsonBuilder] = JsonBuilder, fields: Optional[Sequence[str]] = None):
    super().__init__(builder_class.__name__)
    self.builder_class = builder_class
    self.fields = fields

  def is_instance(self, obj: Any) -> bool:
    return isinstance(obj, self.builder_class) and isinstance(getattr(obj, "builder", None), BuilderDetails)

  def transform(self, obj: JsonBuilder) -> dict:
    return obj.resolve_fields(self.fields)
