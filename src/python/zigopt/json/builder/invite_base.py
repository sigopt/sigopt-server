# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from zigopt.common import *
from zigopt.authorization.empty import EmptyAuthorization  # type: ignore
from zigopt.config.broker import ConfigBroker
from zigopt.invite.service import Invite  # type: ignore
from zigopt.json.builder.json_builder import JsonBuilder, ValidationType, field


class BaseInviteJsonBuilder(JsonBuilder):
  def __init__(self, auth: EmptyAuthorization, invite: Invite, config_broker: ConfigBroker):
    super().__init__()
    self._auth = auth
    self._invite = invite
    self._config_broker = config_broker

  @field(ValidationType.string)
  def email(self) -> str:
    return self._invite.email

  # NOTE: In general we shouldn't show this to the inviting user
  # (because it would allow them to skip email verification),
  # but if we expect the end user to manually provide the invite link to the invitee
  # we must include it.
  # TODO(SN-1111): This should use email_verification_service
  def _should_hide_invite_code(self) -> bool:
    require_email_verification = self._config_broker.get_bool("email.verify", default=True)
    email_enabled = self._config_broker.get_bool("email.enabled", default=True)
    if not require_email_verification and not email_enabled:
      return False
    return True

  def hide_invite_code(self):
    return self._should_hide_invite_code()

  @field(ValidationType.string, hide=hide_invite_code)
  def invite_code(self) -> str:
    return self._invite.invite_code
