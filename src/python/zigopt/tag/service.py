# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import sqlalchemy
from sqlalchemy.orm import Query

from zigopt.common import *
from zigopt.services.base import Service
from zigopt.tag.model import Tag


class TagExistsException(Exception):
  def __init__(self, name: str):
    self.name = name
    super().__init__(f"The tag {self.name} already exists")


class TagService(Service):
  @property
  def tag_query(self) -> Query:
    return self.services.database_service.query(Tag)

  def find_by_client_id_query(self, client_id: int) -> Query:
    return self.tag_query.filter_by(client_id=client_id)

  def find_by_client_and_id_query(self, client_id, tag_id):
    return self.tag_query.filter_by(id=tag_id, client_id=client_id)

  def find_by_client_and_id(self, client_id, tag_id):
    if tag_id is None:
      return None
    return self.services.database_service.one_or_none(
      self.find_by_client_and_id_query(tag_id=tag_id, client_id=client_id),
    )

  def find_by_client_id(self, client_id):
    return self.services.database_service.all(
      self.tag_query.filter_by(client_id=client_id),
    )

  def count_by_client_id(self, client_id):
    return self.services.database_service.count(
      self.tag_query.filter_by(client_id=client_id),
    )

  def insert(self, tag):
    try:
      self.services.database_service.insert(tag)
    except sqlalchemy.exc.IntegrityError as ie:
      self.services.database_service.rollback_session()
      if f'duplicate key value violates unique constraint "{Tag.UNIQUE_NAME_INDEX_NAME}"' in str(ie):
        raise TagExistsException(tag.name) from ie
      raise
    return tag
