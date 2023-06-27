# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections.abc import Mapping, Sequence

from sqlalchemy import desc
from sqlalchemy.orm import Query

from zigopt.db.service import DatabaseService
from zigopt.services.base import Service
from zigopt.web_data.lib import validate_web_data_dict
from zigopt.web_data.model import WebData


def project_query(db_service: DatabaseService, parent_resource_id: Mapping[str, int]) -> Query:
  return (
    db_service.query(WebData)
    .filter(WebData.project_reference_id == parent_resource_id["project"])
    .filter(WebData.project_client_id == parent_resource_id["client"])
  )


queries_by_resource = {"project": project_query}
validate_web_data_dict(queries_by_resource, depth=1)


class WebDataService(Service):
  def count(
    self,
    parent_resource_type: str,
    web_data_type: str,
    parent_resource_id: Mapping[str, int],
    include_deleted: bool = False,
  ) -> int:
    query = (
      queries_by_resource[parent_resource_type](self.services.database_service, parent_resource_id)
      .filter(WebData.deleted == include_deleted)
      .filter(WebData.web_data_type == web_data_type)
    )
    return self.services.database_service.count(query)

  def all(
    self,
    parent_resource_type: str,
    web_data_type: str,
    parent_resource_id: Mapping[str, int],
    include_deleted: bool = False,
  ) -> Sequence[WebData]:
    query = (
      queries_by_resource[parent_resource_type](self.services.database_service, parent_resource_id)
      .filter(WebData.deleted == include_deleted)
      .filter(WebData.web_data_type == web_data_type)
      .order_by(desc(WebData.id))
    )
    return self.services.database_service.all(query)

  def find_by_parent_resource_id_and_id_query(
    self,
    parent_resource_type: str,
    web_data_type: str,
    parent_resource_id: Mapping[str, int],
    base_id: int,
    include_deleted: bool = False,
  ) -> Query:
    query = (
      queries_by_resource[parent_resource_type](self.services.database_service, parent_resource_id)
      .filter(WebData.id == base_id)
      .filter(WebData.deleted == include_deleted)
      .filter(WebData.web_data_type == web_data_type)
    )
    return query

  def find_by_parent_resource_id_and_id(
    self,
    parent_resource_type: str,
    web_data_type: str,
    parent_resource_id: Mapping[str, int],
    base_id: int,
    include_deleted: bool = False,
  ) -> WebData | None:
    query = self.find_by_parent_resource_id_and_id_query(
      parent_resource_type,
      web_data_type,
      parent_resource_id,
      base_id,
      include_deleted,
    )
    return self.services.database_service.one_or_none(query)

  def delete(self, base_id: int) -> int:
    query = self.services.database_service.query(WebData).filter(WebData.id == base_id)
    return self.services.database_service.update_one(query, {"deleted": True})
