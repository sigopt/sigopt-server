# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import sys
import traceback

from zigopt.common import *
from zigopt.common.struct import ImmutableStruct
from zigopt.services.base import Service


FullTraceback = ImmutableStruct("FullTraceback", ("tb_frame", "tb_lineno", "tb_next"))


class SoftException(RuntimeError):
  pass


class _SoftExceptionHandler:
  def __init__(self, handled_exception_type, services, extra):
    self.handled_exception_type = handled_exception_type
    self.services = services
    self.extra = extra

  def _extend_traceback(self, tb, stack):
    for tb_frame, tb_lineno in stack:
      tb = FullTraceback(tb_frame, tb_lineno, tb)
    return tb

  def __enter__(self):
    return None

  def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_type is None:
      return None
    if isinstance(exc_val, self.handled_exception_type):
      current_stack = traceback.walk_stack(sys._getframe().f_back.f_back)  # type: ignore
      full_tb = self._extend_traceback(exc_tb, current_stack)
      self.services.exception_logger.process_soft_exception((exc_type, exc_val, full_tb), extra=self.extra)
      return True
    return False


class AlreadyLoggedException(Exception):
  """
    Used to rethrow an exception that has already been logged and should not
    be logged again
    """

  def __init__(self, underlying):
    super().__init__(str(underlying))
    self.underlying = underlying


class ExceptionLogger(Service):
  def __init__(self, services):
    super().__init__(services)
    self._extra = {}
    self._tracer = None

  def reset_extra(self):
    self._extra = {}

  def add_extra(self, **kwargs):
    extend_dict(self._extra, kwargs)

  def set_tracer(self, tracer):
    self._tracer = tracer

  def log_exception(self, e, extra=None, exc_info=None):
    self.services.logging_service.exception("sigopt.exceptions", e, exc_info, extra)
    if self._tracer and exc_info:
      self._tracer.record_exception(*exc_info, params=extra)

  def _update_extra(self, extra):
    extra = extend_dict({}, self._extra, extra or {})
    extra.update(
      remove_nones(
        {
          "request_id": self.services.logging_service.request_id,
          "trace_id": self.services.logging_service.trace_id,
        }
      )
    )
    return extra

  def tolerate_exceptions(self, exception_type=None, extra=None):
    """
        Use in a `with` block to proceed in the face of exceptions.
        Exceptions will be logged and ignored in production, but thrown in development/testing.
        Use this for situations when you do not expect or desire an exception to occur, but there
        is a straightforward fallback that can be used.

        Example:

        with self.services.exception_logger.tolerate_exceptions(RuntimeError):
          self.some_sketchy_thing()
          return True
        return False

        # If `some_sketchy_thing` succeeds, then True will be returned
        # If `some_sketchy_thing` throws a non-RuntimeError, it will always throw
        # If `some_sketchy_thing` throws a RuntimeError in production,
        #   the error will be logged and False will be returned.
        # If `some_sketchy_thing` throws a RuntimeError in development, the error will be thrown.
        """
    if exception_type is None:
      exception_type = Exception
    extra = self._update_extra(extra)
    return _SoftExceptionHandler(exception_type, self.services, extra)

  def process_soft_exception(self, exc_info, extra=None):
    """
        Propagate an existing error in development, but just log the error and proceed in production.

        :param exc_info: exception info from a ``sys.exc_info()`` call
        :type exc_info: tuple
        :param extra: any extra info you want to log
        :type extra: dict
        """
    self.services.logging_service.exception("sigopt.exceptions", exc_info[1], exc_info)
    if self.services.config_broker.get("features.raiseSoftExceptions", False):
      # pylint: disable=misplaced-bare-raise
      raise
      # pylint: enable=misplaced-bare-raise

  def soft_exception(self, msg, extra=None):
    # Raise an error in development, but just log the error and proceed in production.
    with self.tolerate_exceptions(SoftException, extra=extra):
      raise SoftException(msg)
