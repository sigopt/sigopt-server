# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.handlers.base.handler import Handler
from zigopt.net.errors import BadParamError, NotFoundError


class ClientHandler(Handler):
  def __init__(self, services, request, client_id):
    if client_id is None:
      raise Exception("Client id required")

    self.client_id = client_id
    self.client = None
    super().__init__(services, request)

  def find_objects(self):
    return extend_dict(
      super().find_objects(),
      {
        "client": self._find_client(self.client_id),
      },
    )

  def _find_client(self, client_id):
    if client_id:
      client = self.services.client_service.find_by_id(
        client_id,
        include_deleted=False,
        current_client=self.auth.current_client,
      )
      if client:
        if client.deleted:
          raise BadParamError(f"Cannot perform the requested action on deleted client {client_id}")
        return client
    raise NotFoundError(f"No client {client_id}")

  def can_act_on_objects(self, requested_permission, objects):
    return super().can_act_on_objects(requested_permission, objects) and self.auth.can_act_on_client(
      self.services, requested_permission, objects["client"]
    )
