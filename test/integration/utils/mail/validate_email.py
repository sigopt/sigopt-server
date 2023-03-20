# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from integration.utils.html import validate_html


def validate_email(content_type, text):
  if content_type != "text/plain":
    validate_html(text)
