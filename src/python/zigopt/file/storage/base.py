# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.file.model import File
from zigopt.json.builder import JsonBuilder


class FileStorage:
  def __init__(self, services):
    self.services = services

  def set_file_storage_method(self, file_obj: File) -> None:
    raise NotImplementedError()

  def create_upload_data(self, file_obj: File) -> JsonBuilder:
    raise NotImplementedError()

  def create_download_data(self, file_obj: File) -> JsonBuilder:
    raise NotImplementedError()
