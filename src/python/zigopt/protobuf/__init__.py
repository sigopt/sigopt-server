# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from google.protobuf.message import Message

from zigopt.protobuf.patch import patch_protobuf_class


patch_protobuf_class(Message)
