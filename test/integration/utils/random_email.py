# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common.strings import random_string


def generate_random_email():
  return f"{random_string(str_length=10)}@notsigopt.ninja"
