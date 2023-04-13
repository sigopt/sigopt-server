# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import datetime
import logging

import boto3
from botocore.config import Config as BotoConfig

from zigopt.services.base import Service


class S3UserUploadService(Service):
  DEFAULT_EXPIRATION_SECONDS = datetime.timedelta(hours=1).total_seconds()
  logger = logging.getLogger("sigopt.S3UploadService")

  def __init__(self, services):
    super().__init__(services)
    credentials = {}
    self.s3_client = None
    if self.enabled:
      config_broker = self.services.config_broker
      credentials["endpoint_url"] = config_broker["user_uploads.s3.external_url"]
      credentials["aws_access_key_id"] = config_broker.get("user_uploads.s3.aws_access_key_id")
      credentials["aws_secret_access_key"] = config_broker.get("user_uploads.s3.aws_secret_access_key")
      credentials["aws_session_token"] = None
      self.s3_client = boto3.client(
        "s3",
        config=BotoConfig(signature_version="s3v4"),
        region_name=config_broker.get("user_uploads.s3.region", "us-east-1"),
        **credentials,
      )

  @property
  def enabled(self):
    return self.services.config_broker.get("user_uploads.s3.enabled", False)

  @property
  def expiration_seconds(self):
    return self.services.config_broker.get("user_uploads.s3.expiration_seconds", self.DEFAULT_EXPIRATION_SECONDS)

  def get_bucket(self):
    return self.services.config_broker["user_uploads.s3.bucket"]

  def generate_upload_info(self, key, method, content_length, content_type, content_md5_base64):
    assert self.s3_client is not None
    url = self.s3_client.generate_presigned_url(
      "put_object",
      Params={
        "Bucket": self.get_bucket(),
        "Key": key,
        "ContentDisposition": "attachment",
        "ContentLength": content_length,
        "ContentMD5": content_md5_base64,
        "ContentType": content_type,
      },
      ExpiresIn=int(self.expiration_seconds),
      HttpMethod=method,
    )
    headers = {
      "Content-Disposition": "attachment",
      "Content-Length": str(content_length),
      "Content-MD5": content_md5_base64,
      "Content-Type": content_type,
    }
    return url, headers

  def generate_download_info(self, key):
    assert self.s3_client is not None
    url = self.s3_client.generate_presigned_url(
      "get_object",
      Params={
        "Bucket": self.get_bucket(),
        "Key": key,
      },
      ExpiresIn=int(self.expiration_seconds),
    )
    return url
