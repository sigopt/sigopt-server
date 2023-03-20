# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
class FileStorage:
  def __init__(self, services):
    self.services = services

  def set_file_storage_method(self, file_obj):
    raise NotImplementedError()

  def create_upload_data(self, file_obj):
    raise NotImplementedError()

  def create_download_data(self, file_obj):
    raise NotImplementedError()
