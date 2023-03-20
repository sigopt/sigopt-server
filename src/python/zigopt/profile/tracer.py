# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
class Tracer(object):
  def ignore_transaction(self):
    raise NotImplementedError

  def set_transaction_name(self, name, group=None):
    raise NotImplementedError

  def set_attribute(self, key, value):
    raise NotImplementedError

  def trace_background_task(self, name, group=None):
    raise NotImplementedError

  def record_exception(self, exc, value, tb, params=None):
    raise NotImplementedError


class NullTracer(Tracer):
  def __init__(self):
    pass

  def ignore_transaction(self):
    pass

  def set_transaction_name(self, name, group=None):
    pass

  def set_attribute(self, key, value):
    pass

  def trace_background_task(self, name, group=None):
    return self

  def record_exception(self, exc, value, tb, params=None):
    pass

  def __enter__(self):
    return None

  def __exit__(self, *args, **kwargs):
    pass
