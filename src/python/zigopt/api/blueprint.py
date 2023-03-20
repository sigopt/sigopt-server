# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from flask import Blueprint


class ApiBlueprint(Blueprint):
  def __init__(self, name, app):
    super().__init__(name, __name__)
    self.global_services = app.global_services
    self.request_local_services_factory = app.request_local_services_factory
    self.profiler = app.profiler
    self.tracer = app.tracer
