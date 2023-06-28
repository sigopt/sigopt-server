# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from collections.abc import Sequence
from urllib.parse import urlencode

from zigopt.common import *
from zigopt.authentication.login import PASSWORD_RESET_EXPIRY_IN_HOURS
from zigopt.brand.constant import PRODUCT_NAME
from zigopt.client.model import Client
from zigopt.email.model import HtmlEmail, create_mako_email
from zigopt.organization.model import Organization
from zigopt.services.base import Service
from zigopt.user.model import User


class EmailTemplates(Service):
  def __init__(self, services):
    super().__init__(services)
    self.from_address = self.services.config_broker.get(
      "email.from_address",
      "noreply@sigopt.ninja",
    )
    self.team_name = self.services.config_broker.get("email.team_name", PRODUCT_NAME)
    self.sign_off = "Happy modeling,"
    self.base_template = self.services.config_broker.get("email.base_template")

  @property
  def base_url(self) -> str:
    return self.services.config_broker["address.app_url"].rstrip("/")

  def create(self, template: str, subject: str, to: str, bypass_list_management: bool = False, **kwargs) -> HtmlEmail:
    params = kwargs.copy()
    params["team_name"] = self.team_name
    params["to"] = to
    params["product_name"] = PRODUCT_NAME
    params["sign_off"] = self.sign_off
    return create_mako_email(
      template,
      params=params,
      subject=subject,
      to=to,
      from_address=self.from_address,
      app_url=self.base_url,
      base_template=self.base_template,
      bypass_list_management=bypass_list_management,
    )

  def reset_password_email(self, user: User, code: str) -> HtmlEmail:
    return self.create(
      "./templates/reset_password.mako",
      to=user.email,
      subject=f"{PRODUCT_NAME} Password Reset",
      link=self._change_password_link(code, user.email),
      expiry=PASSWORD_RESET_EXPIRY_IN_HOURS,
      app_url=self.services.config_broker["address.app_url"],
      bypass_list_management=True,
    )

  def no_user_cant_reset_password_email(self, email: str) -> HtmlEmail:
    return self.create(
      "./templates/cant_reset_password.mako",
      to=email,
      subject=f"Could Not Reset {PRODUCT_NAME} Password",
      app_url=self.services.config_broker["address.app_url"],
      reason=f"However, we don't have a record of an account with the email address {email}.",
    )

  def no_password_cant_reset_password_email(self, user: User) -> HtmlEmail:
    return self.create(
      "./templates/cant_reset_password.mako",
      to=user.email,
      subject=f"Could Not Reset {PRODUCT_NAME} Password",
      app_url=self.services.config_broker["address.app_url"],
      reason="However, your password cannot be reset because you use an alternate login method.",
    )

  def user_password_change_email(self, user: User) -> HtmlEmail:
    return self.create(
      "./templates/password_change.mako",
      to=user.email,
      subject=f"{PRODUCT_NAME} Password Changed",
      base_url=self.base_url,
      bypass_list_management=True,
    )

  def verification_email(self, user: User, code: str) -> HtmlEmail:
    return self.create(
      "./templates/verify_email.mako",
      to=user.email,
      subject="Please verify your email address",
      link=self.verify_email_link(code, user.email),
      bypass_list_management=True,
      user_name=user.name,
    )

  def user_email_change_email(self, old_email: str, new_email: str) -> HtmlEmail:
    return self.create(
      "./templates/email_change.mako",
      to=old_email,
      subject=f"{PRODUCT_NAME} Email Address Changed",
      base_url=self.base_url,
      new_email=new_email,
      bypass_list_management=True,
    )

  def verification_reprompt_email(
    self, user: User, organization: Organization, clients: Client, invite_link: str
  ) -> HtmlEmail:
    return self.create(
      "./templates/verification_reprompt.mako",
      to=user.email,
      subject="Please verify your email address",
      link=invite_link,
      organization_name=organization.name,
      clients=clients,
      user_name=user.name,
    )

  def verification_reprompt_owner_email(self, user: User, organization: Organization, invite_link: str) -> HtmlEmail:
    return self.create(
      "./templates/verification_reprompt_owner.mako",
      to=user.email,
      subject="Please verify your email address",
      link=invite_link,
      organization_name=organization.name,
      user_name=user.name,
    )

  def invited_owner_email(self, organization: Organization, email: str, invite_link: str, inviter: User) -> HtmlEmail:
    return self.create(
      "./templates/invited_owner.mako",
      to=email,
      subject=f"You have been invited to {PRODUCT_NAME} as an Organization Owner",
      link=invite_link,
      organization_name=organization.name,
      inviter=inviter,
    )

  def invited_owner_existing_email(self, organization: Organization, email: str, inviter: User) -> HtmlEmail:
    return self.create(
      "./templates/invited_owner_existing.mako",
      to=email,
      subject=f"You have been added to an organization on {PRODUCT_NAME} as an Owner",
      link=self.base_url,
      organization_name=organization.name,
      inviter=inviter,
    )

  def invited_email(
    self, organization: Organization, clients: Client, email: str, invite_link: str, inviter: User
  ) -> HtmlEmail:
    return self.create(
      "./templates/invited.mako",
      to=email,
      subject=f"You have been invited to {PRODUCT_NAME}",
      link=invite_link,
      organization_name=organization.name,
      clients=clients,
      inviter=inviter,
      title="Your team is waiting for you to join them",
    )

  def invited_existing_email(
    self, organization: Organization, clients: Sequence[Client], email: str, inviter: User
  ) -> HtmlEmail:
    return self.create(
      "./templates/invited_existing.mako",
      to=email,
      subject=f"You have been added to an organization on {PRODUCT_NAME}",
      link=self.base_url,
      organization_name=organization.name,
      clients=clients,
      inviter=inviter,
    )

  def welcome_email(self, user: User) -> HtmlEmail:
    return self.create(
      "./templates/welcome_email.mako",
      to=user.email,
      subject=f"Welcome to {PRODUCT_NAME}!",
      user_name=user.name,
      app_url=self.services.config_broker["address.app_url"],
      title=f"Welcome to {PRODUCT_NAME}, {user.name}!",
    )

  def existing_email(self, user: User) -> HtmlEmail:
    return self.create(
      "./templates/existing_email.mako",
      to=user.email,
      subject=f"{PRODUCT_NAME} signup attempt",
      app_url=self.services.config_broker["address.app_url"],
    )

  def _make_url(self, page: str, code: str, email: str) -> str:
    url_params = self._url_params([("code", code), ("email", email)])
    return f"{self.base_url}/{page}?{url_params}"

  def _change_password_link(self, code: str, email: str) -> str:
    return self._make_url("change_password", code, email)

  def verify_email_link(self, code: str, email: str) -> str:
    return self._make_url("verify", code, email)

  def accept_invite_link(self, code: str, email: str, organization: str) -> str:
    return self._make_url("signup", code, email)

  def _url_params(self, params: Sequence[tuple[str, str]]) -> str:
    return urlencode([(k.encode("utf-8"), v.encode("utf-8")) for k, v in params if v is not None])

  def login_ratelimit(self, email: str) -> HtmlEmail:
    return self.create(
      "./templates/login_ratelimit.mako",
      to=email,
      subject=f"{PRODUCT_NAME} Account Locked",
      app_url=self.services.config_broker["address.app_url"],
      bypass_list_management=True,
    )
