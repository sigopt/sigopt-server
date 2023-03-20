# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import pytest

from zigopt.file.model import File
from zigopt.protobuf.gen.file.filedata_pb2 import FileData


@pytest.mark.parametrize(
  "mime_type,expected_extension",
  [
    ("text/plain", ".txt"),
    ("image/jpeg", ".jpg"),
    ("image/png", ".png"),
    ("image/svg+xml", ".svg"),
    ("unknown", ""),
  ],
)
def test_get_download_filename_without_filename(mime_type, expected_extension):
  file_data = FileData(content_type=mime_type)
  file_obj = File(name="some file", data=file_data, created_by=None, client_id=None)
  assert file_obj.get_download_filename() == f"somefile{expected_extension}"


@pytest.mark.parametrize(
  "filename,expected_filename",
  [
    ("test.jpeg", "test.jpeg"),
    ("/root/.cache/hello.svg", "hello.svg"),
    ("~/Pictures/DCIM/02145xyz.jpg~", "02145xyz.jpg"),
    ("C:\\Users\\SigOpt\\Pictures\\Wallpaper\\background.bmp", "background.bmp"),
  ],
)
def test_get_download_filename_with_filename(filename, expected_filename):
  file_data = FileData(content_type="image/png")
  file_obj = File(name="some file", filename=filename, data=file_data, created_by=None, client_id=None)
  assert file_obj.get_download_filename() == expected_filename


def test_get_download_filename_without_name_and_filename():
  file_data = FileData(content_type="image/png")
  file_obj = File(id=1234, name=None, data=file_data, created_by=None, client_id=None)
  assert file_obj.get_download_filename() == "1234.png"
