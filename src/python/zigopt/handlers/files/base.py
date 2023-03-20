# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.handlers.base.handler import Handler
from zigopt.json.builder import FileJsonBuilder
from zigopt.net.errors import NotFoundError
from zigopt.protobuf.gen.token.tokenmeta_pb2 import TokenMeta


class FileHandler(Handler):
  permitted_scopes = tuple([TokenMeta.ALL_ENDPOINTS])

  def __init__(self, services, request, file_id):
    if file_id is None:
      raise Exception("File id required")
    self.client = None
    self.file = None
    self.file_id = file_id
    super().__init__(services, request)

  def prepare(self):
    if not self.services.file_service.enabled:
      raise NotFoundError()
    return super().prepare()

  def get_file_not_found_error(self):
    raise NotFoundError(f"File with id {self.file_id} not found.")

  def find_objects(self):
    objects = super().find_objects()
    file_obj = self.services.file_service.find_by_id(self.file_id)
    if file_obj is None:
      raise self.get_file_not_found_error()
    objects["file"] = file_obj
    client = self.services.client_service.find_by_id(file_obj.client_id)
    objects["client"] = client
    return objects

  def can_act_on_objects(self, requested_permission, objects):
    return super().can_act_on_objects(requested_permission, objects) and self.auth.can_act_on_file(
      self.services, requested_permission, objects["file"], client=objects["client"]
    )

  def get_file_json_builder(self):
    download_data = self.services.file_service.create_download_data(self.file)
    return FileJsonBuilder(self.file, download_info=download_data)
