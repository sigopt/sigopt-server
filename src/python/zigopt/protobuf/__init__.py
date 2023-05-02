# Copyright © 2023 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from google.protobuf.message import Message


# NOTE: In order for crosshair to instantiate a Message, it calls the __deepcopy__ method, which in turn calls MergeFrom
# which raises NotImplementedError. This allows crosshair to instantiate a Message for fuzz testing.
Message.MergeFrom = lambda self, other: None  # type: ignore
