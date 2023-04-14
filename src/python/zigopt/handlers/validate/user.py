# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from typing import Optional

from zigopt.handlers.validate.base import validate_email, validate_name
from zigopt.user.model import User

from libsigopt.aux.errors import InvalidValueError, MissingParamError


def validate_user_name(name: Optional[str]) -> str:
  name = validate_name(name)
  if name:
    if len(name) >= User.NAME_MAX_LENGTH:
      raise InvalidValueError(f"Name must be fewer than {User.NAME_MAX_LENGTH} characters")
    return name
  raise MissingParamError("name", "User name is required")


def validate_user_email(email: Optional[str]) -> str:
  email = validate_email(email)
  if len(email) >= User.EMAIL_MAX_LENGTH:
    raise InvalidValueError(f"Email must be fewer than {User.EMAIL_MAX_LENGTH} characters")
  return email


def validate_user_password(plaintext_password: str) -> str:
  # TODO(SN-1105): This is not quite right. Really we should be comparing len(plaintext_password.encode('utf-8'))
  # instead of len(plaintext_password), so that we are counting utf-8 encoded bytes, not characters.
  # However it's not a huge deal, it just means that if the byte length is > 72 then only the first 72 bytes are
  # used to check if the password is correct.
  # We could count bytes, but conveying that to the user in an error message would be annoying
  if len(plaintext_password) >= User.PASSWORD_MAX_LENGTH_BYTES:
    raise InvalidValueError(f"Password must be fewer than {User.PASSWORD_MAX_LENGTH_BYTES} characters")

  is_long_enough = len(plaintext_password) >= User.PASSWORD_MIN_LENGTH_CHARACTERS
  has_num = any((c.isnumeric() for c in plaintext_password))
  has_lower = any((c.islower() for c in plaintext_password))
  has_upper = any((c.isupper() for c in plaintext_password))
  has_special = any((not c.isalnum() for c in plaintext_password))
  if not all((is_long_enough, has_num, has_lower, has_upper, has_special)):
    raise InvalidValueError(
      "Password must be"
      f" more than {User.PASSWORD_MIN_LENGTH_CHARACTERS} characters"
      ", and contain an uppercase character, a lowercase character, a digit, and a special character."
    )

  return plaintext_password
