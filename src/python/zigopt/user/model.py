# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import bcrypt
from sqlalchemy import BigInteger, Column, String
from sqlalchemy.orm import validates

from zigopt.common import *
from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
from zigopt.db.declarative import Base
from zigopt.protobuf.gen.user.usermeta_pb2 import UserMeta


def normalize_email(email):
  return email.strip().lower()


def get_domain_from_email(email):
  # Use rsplit, since emails can technically have multiple @ signs
  _, domain = normalize_email(email).rsplit("@", 1)
  return domain


class User(Base):
  NAME_MAX_LENGTH = 100
  EMAIL_MAX_LENGTH = 100
  PASSWORD_MAX_LENGTH_BYTES = 72  # Comes from bcrypt, passwords longer than this are truncated
  PASSWORD_MIN_LENGTH_CHARACTERS = 8

  __tablename__ = "users"

  id = Column(BigInteger, primary_key=True)
  name = Column(String)
  email = Column(String, index=True, unique=True)
  hashed_password = Column(String)
  user_meta = ProtobufColumn(UserMeta, name="user_meta_json", nullable=False)

  @validates("user_meta")
  def validator(self, key, meta):
    return ProtobufColumnValidator(meta)

  def __init__(self, *args, **kwargs):
    if "hashed_password" not in kwargs:
      kwargs["hashed_password"] = password_hash(kwargs.pop("plaintext_password", None))
    else:
      assert "plaintext_password" not in kwargs
    kwargs["user_meta"] = kwargs.get("user_meta", User.user_meta.default_value())
    super().__init__(*args, **kwargs)

  @validates("email")
  def validate_email(self, key, email):
    assert is_string(email)
    assert "@" in email
    return normalize_email(email)

  @property
  def has_verified_email(self):
    return self.user_meta.has_verified_email

  @property
  def is_educational_user(self):
    return self.user_meta.educational_user

  @property
  def date_created(self):
    return self.user_meta.GetFieldOrNone("date_created")

  @property
  def deleted(self):
    return self.user_meta.deleted

  @property
  def needs_password_reset(self):
    return self.user_meta.needs_password_reset

  @property
  def hashed_password_reset_code(self):
    return self.user_meta.GetFieldOrNone("hashed_password_reset_code")

  @property
  def password_reset_timestamp(self):
    return self.user_meta.GetFieldOrNone("password_reset_timestamp")

  @property
  def hashed_email_verification_code(self):
    return self.user_meta.GetFieldOrNone("hashed_email_verification_code")

  @property
  def email_verification_timestamp(self):
    return self.user_meta.email_verification_timestamp

  @property
  def planned_usage(self):
    return self.user_meta.planned_usage

  @property
  def show_welcome(self):
    return self.user_meta.show_welcome


def password_matches(plaintext, hashed):
  encoded_plaintext = plaintext.encode("utf-8")
  encoded_hashed = hashed.encode("utf-8")
  return bcrypt.hashpw(encoded_plaintext, encoded_hashed) == encoded_hashed


# Default work_factor is 14, which is currently recognized as sufficiently slow to thwart brute-forcing
# It should not be lower than that, but we expose this parameter to make hashing faster for testing
DEFAULT_WORK_FACTOR = 14
PREVIOUS_WORK_FACTORS = []


def _get_work_factor(work_factor=None):
  return coalesce(work_factor, DEFAULT_WORK_FACTOR)


def password_hash(plaintext, work_factor=None):
  work_factor = _get_work_factor(work_factor)
  if plaintext:
    encoded_plaintext = plaintext.encode("utf-8")
    return bcrypt.hashpw(encoded_plaintext, bcrypt.gensalt(work_factor)).decode("ascii")
  return None


def do_password_hash_work_factor_update(services, user, plaintext_password):
  if not user or not user.hashed_password:
    services.exception_logger.log_exception(
      f"Should not be updating password if no user or no password: user={user and user.id}",
    )
    return
  desired_work_factor = _get_work_factor(services.config_broker.get("user.password_work_factor"))
  # dev/test uses "5" but hash formats it as "05"
  desired_work_factor_str = f"{desired_work_factor:02}"
  previous_work_factor_strs = [str(f) for f in PREVIOUS_WORK_FACTORS]
  try:
    empty, alg, found_work_factor, output, *_ = user.hashed_password.split("$")
    if (
      empty != ""
      or alg not in ("2a", "2b")
      or found_work_factor not in (*previous_work_factor_strs, desired_work_factor_str)
      or output == ""
    ):
      raise ValueError("unexpected password hash fields")
    if found_work_factor in previous_work_factor_strs:
      new_hashed = password_hash(plaintext_password, desired_work_factor)
      services.database_service.update_one(
        services.database_service.query(User).filter(User.id == user.id), {User.hashed_password: new_hashed}
      )
  except ValueError:
    services.exception_logger.log_exception(
      f"unexpected password format for user {user.id}",
    )
