# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.net.errors import BadParamError  # type: ignore
from zigopt.user.model import get_domain_from_email, normalize_email  # type: ignore


def has_invalid_chars(text: str) -> bool:
  """
    Searches for characters which should not reasonably be provided to the API
    """
  return any((ord(t) < 32 for t in text))


def validate_name(name: Optional[str]) -> str:
  """
    Validates a user-entered name
    """
  if name is None:
    raise BadParamError("Invalid name: cannot be null")
  if name == "":
    raise BadParamError("Invalid name: cannot be empty")
  if has_invalid_chars(name):
    raise BadParamError(f"Invalid name: {name}")
  return name.strip()


def validate_email_domain(domain: str) -> str:
  if has_invalid_chars(domain) or "@" in domain:
    raise BadParamError(f"Invalid email domain: {domain}")
  return normalize_email(domain)


def validate_email(email: Optional[str]) -> str:
  if email is None:
    raise BadParamError("Invalid email: cannot be null")
  if has_invalid_chars(email) or "@" not in email:
    raise BadParamError(f"Invalid email: {email}")
  validate_email_domain(get_domain_from_email(email))
  return normalize_email(email)


def validate_period(start: Optional[int], end: Optional[int]) -> tuple[Optional[int], Optional[int]]:
  """
    Validates a period of time, as specified by a start and end timestamp
    """
  if start and start < 0:
    raise BadParamError("Invalid period start timestamp: cannot be less than 0")
  if end and end < 0:
    raise BadParamError("Invalid period end timestamp: cannot be less than 0")
  if start and end and end < start:
    raise BadParamError("Invalid period range: end timestamp cannot be before start timestamp")

  return (start, end)
