# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import json

import boto3
import pytest
from botocore.exceptions import ClientError as AWSError

from integration.web.test_base import WebBase


class TestCookie(WebBase):
  @pytest.fixture
  def cookiejar_bucket(self, config_broker):
    return config_broker["web.cookiejar_bucket"]

  @pytest.fixture
  def cookie_name(self, config_broker):
    return config_broker.get("web.cookie_name", "sigopt-session-id")

  @pytest.fixture
  def s3_client(self, config_broker):
    options = {}
    url = config_broker.get("web.cookiejar_endpoint")
    if url:
      options["endpoint_url"] = url
    access_credentials = config_broker.get("web.cookiejar_credentials")
    if access_credentials:
      options["aws_access_key_id"] = access_credentials["accessKeyId"]
      options["aws_secret_access_key"] = access_credentials["secretAccessKey"]
    region = config_broker.get("web.cookiejar_region")
    if region:
      options["region_name"] = region
    return boto3.client(
      "s3",
      **options,
    )

  @pytest.mark.parametrize(
    "invalid_session_id",
    [
      "",
      "xyz123",
      "eHl6MTIzCg==",
      "eHl6MTIzCg..",
      "YWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYWFhYQ==",
    ],
  )
  def test_invalid_session_id(self, cookie_name, web_connection, invalid_session_id):
    response_cookies = web_connection.get("/", cookies={cookie_name: invalid_session_id}).response.cookies
    new_session_id = response_cookies.get(cookie_name)
    assert new_session_id != invalid_session_id
    assert len(new_session_id) == 88
    assert new_session_id.endswith("..")

  def test_corrupt_cookie_in_cookiejar(self, s3_client, cookie_name, web_connection, cookiejar_bucket, config_broker):
    response = web_connection.get("/cookie").response
    session_id = response.cookies.get(cookie_name)
    assert json.load(s3_client.get_object(Bucket=cookiejar_bucket, Key=session_id)["Body"]) == response.json()
    s3_client.put_object(Bucket=cookiejar_bucket, Key=session_id, Body="invalid json")
    web_connection.get("/")
    response = web_connection.get("/cookie").response
    session_id = response.cookies.get(cookie_name)
    assert json.load(s3_client.get_object(Bucket=cookiejar_bucket, Key=session_id)["Body"]) == response.json()

  def check_cookie_was_deleted(self, s3_client, session_id, cookiejar_bucket):
    with pytest.raises(AWSError) as aws_error:
      s3_client.head_object(Bucket=cookiejar_bucket, Key=session_id)
    assert aws_error.value.response["Error"]["Code"] == "404"

  def test_rotate_session_id_on_login(self, s3_client, cookie_name, web_connection, cookiejar_bucket):
    web_connection.get("/")
    session_id = web_connection.cookies.get(cookie_name)
    web_connection.login()
    assert web_connection.cookies.get(cookie_name) != session_id
    self.check_cookie_was_deleted(s3_client, session_id, cookiejar_bucket)

  def test_rotate_session_id_on_logout(self, s3_client, cookie_name, logged_in_web_connection, cookiejar_bucket):
    web_connection = logged_in_web_connection
    csrf_token = web_connection.get("/cookie").response.json()["loginState"]["csrfToken"]
    session_id = web_connection.cookies.get(cookie_name)
    web_connection.post(
      "/logout", data=f"csrf_token={csrf_token}", headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert web_connection.cookies.get(cookie_name) != session_id
    self.check_cookie_was_deleted(s3_client, session_id, cookiejar_bucket)
