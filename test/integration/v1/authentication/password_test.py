# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
from http import HTTPStatus

import pytest
from requests.exceptions import HTTPError

from zigopt.token.model import Token, TokenType
from zigopt.user.model import User

from integration.auth import AuthProvider
from integration.base import RaisesApiException
from integration.connection import IntegrationTestConnection
from integration.utils.constants import NEW_USER_EMAIL_SEARCH_TERM
from integration.utils.emails import extract_password_reset_code, extract_verify_code
from integration.v1.test_base import V1Base


class PasswordTest(V1Base):
  @pytest.fixture
  def credentials(self, connection):
    return connection.email, connection.password

  @pytest.fixture
  def expired_reset_credentials(self, services, api, config_broker, auth_provider, anonymous_connection, inbox):
    connection = self.make_v1_connection(config_broker, api, auth_provider)
    reset_code = self.get_reset_code(anonymous_connection, connection.email, inbox)
    email = connection.email.lower()
    user = services.database_service.one(services.database_service.query(User).filter(User.email == email))
    meta = user.user_meta
    meta.password_reset_timestamp = 0
    services.database_service.update(
      services.database_service.query(User).filter(User.id == user.id),
      {User.user_meta: meta},
    )
    return connection.email, reset_code

  @pytest.fixture
  def reset_code(self, config_broker, credentials, anonymous_connection, inbox):
    email, _ = credentials
    return self.get_reset_code(anonymous_connection, email, inbox)

  def get_reset_code(self, anonymous_connection, email, inbox):
    anonymous_connection.sessions().delete(email=email)
    return extract_password_reset_code(inbox, email)

  def verify_password_was_changed(
    self,
    anonymous_connection,
    connection,
    email,
    old_password,
    new_password,
    config_broker,
  ):
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.sessions().create(email=email, password=old_password)
    session = anonymous_connection.sessions().create(email=email, password=new_password)
    assert session.user.id
    assert session.api_token.token
    assert session.api_token.token != connection.user_token
    assert session.client.id == connection.client_id
    assert not session.needs_password_reset


class TestChangePassword(PasswordTest):
  def test_change_password_logged_in(self, credentials, anonymous_connection, connection, config_broker):
    email, password = credentials
    new_password = AuthProvider.randomly_generated_password()
    connection.sessions().update(
      **{
        "old_password": password,
        "new_password": new_password,
      }
    )
    self.verify_password_was_changed(anonymous_connection, connection, email, password, new_password, config_broker)

  @pytest.mark.parametrize(
    "invalid_password",
    [
      "Short9!",
      "NoDigitInThisPassword!",
      "NoSpecialCharacterInThisPassword9",
      "nouppercaseinthispassword9!",
      "NOLOWERCASEINTHISPASSWORD9!",
      "ThisPasswordIsTooLong!9" * 10,
    ],
  )
  def test_invalid_password(self, credentials, connection, config_broker, invalid_password):
    email, password = credentials
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.sessions().update(
        **{
          "email": email,
          "old_password": password,
          "new_password": invalid_password,
        }
      )

  def test_password_reuse(self, credentials, connection):
    email, password = credentials
    with RaisesApiException(HTTPStatus.FORBIDDEN):
      connection.sessions().update(
        **{
          "email": email,
          "old_password": password,
          "new_password": password,
        }
      )


class TestChangePasswordFailures(PasswordTest):
  def test_verify_only(self, connection):
    password = connection.password
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      connection.sessions().update(
        **{
          "email": connection.email,
          "old_password": password,
          "verify_password": "new password",
        }
      )

  def test_invalid_email(self, anonymous_connection, reset_code):
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      anonymous_connection.sessions().update(
        **{
          "email": AuthProvider.randomly_generated_email(),
          "password_reset_code": reset_code,
          "new_password": AuthProvider.randomly_generated_password(),
        }
      )
    # NOTE: We do not reveal that the email is invalid, to avoid
    # unauthorized guesses at emails
    assert e.value.to_json()["message"] == "Invalid email/password_reset_code"

  def test_wrong_email(self, connection, credentials):
    _, password = credentials
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.sessions().update(
        **{
          "email": AuthProvider.randomly_generated_email(),
          "old_password": password,
          "new_password": AuthProvider.randomly_generated_password(),
        }
      )
    assert e.value.to_json()["message"] == "Invalid email parameter when authenticating with API token"

  def test_wrong_password(self, anonymous_connection, credentials):
    email, _ = credentials
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.sessions().update(
        **{
          "email": email,
          "old_password": "wrong password",
          "new_password": AuthProvider.randomly_generated_password(),
        }
      )

  def test_no_old_password(self, anonymous_connection, credentials):
    email, _ = credentials
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.sessions().update(
        **{
          "email": email,
          "new_password": AuthProvider.randomly_generated_password(),
        }
      )


class TestLoggedOutPassword(PasswordTest):
  def test_invalid_password_request(self, anonymous_connection, inbox, config_broker):
    email = AuthProvider.randomly_generated_email()
    anonymous_connection.sessions().delete(email=email)
    inbox.wait_for_email(email, search_term="have a record of an account")

  def test_email_code(self, anonymous_connection, connection, credentials, reset_code, config_broker):
    email, old_password = credentials
    new_password = AuthProvider.randomly_generated_password()
    anonymous_connection.sessions().update(
      **{
        "email": email,
        "password_reset_code": reset_code,
        "new_password": new_password,
      }
    )
    self.verify_password_was_changed(anonymous_connection, connection, email, old_password, new_password, config_broker)

  @pytest.mark.slow
  def test_email_code_verified(self, anonymous_connection, config_broker, inbox, api_url, api, auth_provider):
    connection = self.make_v1_connection(config_broker, api, auth_provider, has_verified_email=False)
    user = connection.users(connection.user_id).fetch()
    assert not user.has_verified_email
    email = user.email
    anonymous_connection.verifications().create(email=email)
    verify_code = extract_verify_code(inbox, email)
    anonymous_connection.sessions().create(code=verify_code, email=email)
    user = connection.users(connection.user_id).fetch()
    assert user.has_verified_email
    assert connection.users(connection.user_id).permissions().fetch().count == 1
    inbox.wait_for_email(email, search_term=NEW_USER_EMAIL_SEARCH_TERM)

    new_password = AuthProvider.randomly_generated_password()
    reset_code = self.get_reset_code(anonymous_connection, email, inbox)
    session = anonymous_connection.sessions().update(
      **{
        "email": email,
        "password_reset_code": reset_code,
        "new_password": new_password,
      }
    )
    assert not session.needs_password_reset
    self.verify_password_was_changed(
      anonymous_connection,
      connection,
      email,
      connection.password,
      new_password,
      config_broker,
    )
    new_connection = IntegrationTestConnection(api_url=api_url, api=api, user_token=session.api_token.token)
    assert new_connection.users(session.user.id).permissions().fetch().count == 1

    inbox.wait_for_email(email, search_term="recently changed")

  def test_email_code_unverified(self, anonymous_connection, inbox, config_broker):
    if config_broker.get("features.requireInvite"):
      pytest.skip()
    email = AuthProvider.randomly_generated_email()
    old_password = AuthProvider.randomly_generated_password()
    new_password = AuthProvider.randomly_generated_password()
    new_user = anonymous_connection.users().create(name="new user", email=email, password=old_password)
    assert not new_user.has_verified_email
    reset_code = self.get_reset_code(anonymous_connection, email, inbox)
    session = anonymous_connection.sessions().update(
      **{
        "email": email,
        "password_reset_code": reset_code,
        "new_password": new_password,
      }
    )
    assert session.user.id == new_user.id
    assert session.user.email == new_user.email
    assert session.user.has_verified_email is True
    assert session.client.id
    assert session.api_token.token

    login_session = anonymous_connection.sessions().create(email=email, password=new_password)
    assert login_session.user.id == new_user.id
    assert login_session.client.id == session.client.id
    assert login_session.api_token.token != session.api_token.token
    assert login_session.api_token.lease_length > 0
    assert login_session.api_token.expires >= session.api_token.expires

    inbox.wait_for_email(email, search_term="recently changed")
    inbox.wait_for_email(email, search_term=NEW_USER_EMAIL_SEARCH_TERM)


class TestTimeoutPassword(PasswordTest):
  def test_active_reset_code(self, request, anonymous_connection, connection, credentials, reset_code, config_broker):
    email, old_password = credentials
    new_password = AuthProvider.randomly_generated_password()
    anonymous_connection.sessions().update(
      **{
        "email": email,
        "password_reset_code": reset_code,
        "new_password": new_password,
      }
    )
    self.verify_password_was_changed(
      anonymous_connection,
      connection,
      email,
      old_password,
      new_password,
      config_broker,
    )


class TestLoggedOutPasswordFailures(PasswordTest):
  def test_email_no_code(self, anonymous_connection, credentials):
    email, _ = credentials
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.sessions().update(
        **{
          "email": email,
          "new_password": AuthProvider.randomly_generated_password(),
        }
      )

  def test_invalid_email(self, anonymous_connection, reset_code):
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      anonymous_connection.sessions().update(
        **{
          "email": AuthProvider.randomly_generated_email(),
          "password_reset_code": reset_code,
          "new_password": AuthProvider.randomly_generated_password(),
        }
      )
    # NOTE: We do not reveal that the email is invalid, to avoid
    # unauthorized guesses at emails
    assert e.value.to_json()["message"] == "Invalid email/password_reset_code"

  def test_email_wrong_code(self, anonymous_connection, credentials, reset_code):
    email, _ = credentials
    with RaisesApiException(HTTPStatus.BAD_REQUEST):
      anonymous_connection.sessions().update(
        **{
          "email": email,
          "password_reset_code": reset_code + "aaa",
          "new_password": AuthProvider.randomly_generated_password(),
        }
      )

  def test_expired_reset_code(self, request, anonymous_connection, expired_reset_credentials, inbox):
    email, reset_code = expired_reset_credentials
    with RaisesApiException(HTTPStatus.UNAUTHORIZED) as e:
      anonymous_connection.sessions().update(
        **{
          "email": email,
          "password_reset_code": reset_code,
          "new_password": AuthProvider.randomly_generated_password(),
        }
      )
    msg = e.value.to_json()["message"]
    assert msg == "Expired password_reset_code"

  def test_invalidating_old_reset_code(self, anonymous_connection, credentials, reset_code):
    email, _ = credentials
    anonymous_connection.sessions().delete(email=email)
    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      anonymous_connection.sessions().update(
        **{
          "email": email,
          "password_reset_code": reset_code,  # old reset_code
          "new_password": AuthProvider.randomly_generated_password(),
        }
      )
    msg = e.value.to_json()["message"]
    assert msg == "Invalid email/password_reset_code"

  # NOTE: while it seems odd to rate limit someone on changing their password when they're already logged in,
  # we don't want someone who hijacks a session to be able to brute force the logged in users password
  @pytest.mark.slow
  def test_password_change_rate_limit(self, connection, credentials, services):
    email, old_password = credentials
    tries = 2 * services.rate_limiter.login_max_attempts + 1
    with pytest.raises(HTTPError) as excinfo:
      for _ in range(tries):
        try:
          connection.raw_request(
            "PUT",
            "/v1/sessions",
            json={
              "email": email,
              "old_password": old_password + "a",
              "new_password": AuthProvider.randomly_generated_password(),
            },
          ).raise_for_status()
        except HTTPError as e:
          if e.response.status_code != HTTPStatus.BAD_REQUEST:
            raise e
    assert excinfo.value.response.status_code == HTTPStatus.TOO_MANY_REQUESTS


class TestSessionCreate(PasswordTest):
  def test_session_create(self, credentials, anonymous_connection, inbox, global_services):
    email, right_password = credentials

    anonymous_connection.raw_request(
      "POST", "/v1/sessions", json=dict(email=email, password=right_password)
    ).raise_for_status()

  def test_no_password(self, anonymous_connection, db_connection, api_url, api, inbox):
    email = AuthProvider.randomly_generated_email()
    user = User(
      name="okta",
      email=email,
      plaintext_password=None,
    )
    db_connection.insert(user)
    assert user.hashed_password is None

    token = Token(user_id=user.id, token_type=TokenType.USER)
    db_connection.insert(token)

    connection = IntegrationTestConnection(api_url=api_url, api=api, user_token=token.token)

    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      anonymous_connection.sessions().create(email=email, password="password")
    assert e.value.to_json()["message"] == "Invalid email/password"

    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      anonymous_connection.sessions().create(email=email, password=None)
    assert e.value.to_json()["message"] == "Invalid email/password"

    with RaisesApiException(HTTPStatus.BAD_REQUEST) as e:
      connection.users(user.id).update(email=AuthProvider.randomly_generated_email())
    assert "your account is externally administered" in e.value.to_json()["message"]

    assert not inbox.check_email(email)
    anonymous_connection.sessions().delete(email=email)
    (message,) = inbox.wait_for_email(email)
    assert "cannot be reset because you use an alternate login method" in message
