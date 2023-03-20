# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from pprint import pformat

from sqlalchemy.ext.declarative import declarative_base


class SQLAPrintMixin(object):
  def __str__(self):
    return pformat(self._asdict())

  def __repr__(self):
    attributes = self._table_data()
    return self.__class__.__name__ + "(" + ", ".join(attr[0] + "=" + repr(attr[1]) for attr in attributes) + ")"

  def _table_data(self):
    attributes = []
    for key in self.__table__.columns.keys():
      if hasattr(self, key):
        value = getattr(self, key)
        attributes.append((key, value))
    return attributes

  def _asdict(self):
    return dict(self._table_data())


Base = declarative_base(cls=SQLAPrintMixin)
