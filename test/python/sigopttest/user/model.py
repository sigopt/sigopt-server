# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# -*- coding: utf-8 -*-

from zigopt.user.model import password_hash, password_matches


def test_password():
  plaintext_1 = "password"
  plaintext_2 = "different"
  hashed_1 = password_hash(plaintext_1, work_factor=5)
  hashed_2 = password_hash(plaintext_2, work_factor=5)

  unicode_plaintext_1 = "king 👑  password"
  unicode_plaintext_2 = "alien 👽  password"
  hashed_unicode_1 = password_hash(unicode_plaintext_1, work_factor=5)
  hashed_unicode_2 = password_hash(unicode_plaintext_2, work_factor=5)

  assert password_matches(plaintext_1, hashed_1)
  assert not password_matches(plaintext_2, hashed_1)
  assert not password_matches(unicode_plaintext_1, hashed_1)
  assert not password_matches(unicode_plaintext_2, hashed_1)
  assert not password_matches("wrong", hashed_1)

  assert not password_matches(plaintext_1, hashed_2)
  assert password_matches(plaintext_2, hashed_2)
  assert not password_matches(unicode_plaintext_1, hashed_2)
  assert not password_matches(unicode_plaintext_2, hashed_2)
  assert not password_matches("wrong", hashed_2)

  assert not password_matches(plaintext_1, hashed_unicode_1)
  assert not password_matches(plaintext_2, hashed_unicode_1)
  assert password_matches(unicode_plaintext_1, hashed_unicode_1)
  assert not password_matches(unicode_plaintext_2, hashed_unicode_1)
  assert not password_matches("wrong", hashed_unicode_1)

  assert not password_matches(plaintext_1, hashed_unicode_2)
  assert not password_matches("different", hashed_unicode_2)
  assert not password_matches(unicode_plaintext_1, hashed_unicode_2)
  assert password_matches(unicode_plaintext_2, hashed_unicode_2)
  assert not password_matches("wrong", hashed_unicode_2)
