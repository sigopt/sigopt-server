# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import mock
import pytest

from zigopt.common import *
from zigopt.api.auth import always_fail_authentication
from zigopt.authorization.constant import AuthorizationDenied
from zigopt.authorization.empty import EmptyAuthorization
from zigopt.handlers.base.handler import *
from zigopt.net.errors import ForbiddenError, NotFoundError
from zigopt.net.responses import TokenStatus
from zigopt.protobuf.gen.token.tokenmeta_pb2 import READ


OBJECT = object()
PARAMS = object()
KEY = object()
RESPONSE = object()


def always_succeed_authentication(services, request):
  return EmptyAuthorization()


class HandlerWithObject(Handler):
  allow_development = False
  authenticator = staticmethod(always_succeed_authentication)
  required_permissions = READ

  def __init__(self, services, request):
    super().__init__(services, request)
    self.key = None

  def find_objects(self):
    return extend_dict(
      super().find_objects(),
      {
        "key": KEY,
      },
    )

  def can_act_on_objects(self, requested_permission, objects):
    return super().can_act_on_objects(requested_permission, objects) and objects["key"] is KEY

  def handle(self):
    return RESPONSE


class HandlerWithoutObject(Handler):
  allow_development = False
  authenticator = staticmethod(always_succeed_authentication)
  required_permissions = READ

  def handle(self):
    return RESPONSE


@pytest.mark.parametrize("BaseHandler", [HandlerWithObject, HandlerWithoutObject])
class TestHandler(object):
  @pytest.fixture
  def services(self):
    return mock.Mock()

  @pytest.fixture
  def req(self):
    return mock.Mock()

  def test_handler_no_params(self, services, req, BaseHandler):
    handler = BaseHandler(services, req)
    handler.prepare()
    assert handler.parse_params(req) is Handler.NO_PARAMS
    assert handler.handle() is RESPONSE

  def test_handler_with_params(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      def parse_params(self, request):
        return PARAMS

      def handle(self, params):
        assert params is PARAMS
        return RESPONSE

    handler = ChildHandler(services, req)
    handler.prepare()
    params = handler.parse_params(req)
    assert handler.handle(params) is RESPONSE

  def test_authenticator(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      authenticator = always_fail_authentication

    handler = ChildHandler(services, req)
    with pytest.raises(ForbiddenError):
      handler.prepare()

  def test_cannot_act_on_objects(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      def __init__(self, services, request):
        super().__init__(services, request)
        self.object = None

      def find_objects(self):
        return extend_dict(
          super().find_objects(),
          {
            "object": OBJECT,
          },
        )

      def can_act_on_objects(self, requested_permission, objects):
        assert objects["object"] is OBJECT
        return False

    handler = ChildHandler(services, req)
    with pytest.raises(NotFoundError):
      handler.prepare()
    assert handler.object is None

  def test_needs_email_verification(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      def __init__(self, services, request):
        super().__init__(services, request)
        self.object = None

      def find_objects(self):
        return extend_dict(
          super().find_objects(),
          {
            "object": OBJECT,
          },
        )

      def can_act_on_objects(self, requested_permission, objects):
        assert objects["object"] is OBJECT
        return AuthorizationDenied.NEEDS_EMAIL_VERIFICATION

    handler = ChildHandler(services, req)
    with pytest.raises(NotFoundError) as e:
      handler.prepare()
    assert handler.object is None
    assert e.value.token_status == TokenStatus.NEEDS_EMAIL_VERIFICATION

  def test_forgot_can_act_on_objects(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      def __init__(self, services, request):
        super().__init__(services, request)
        self.test_other_key = None

      def find_objects(self):
        return extend_dict(
          super().find_objects(),
          {
            "test_other_key": KEY,
          },
        )

    with pytest.raises(InconsistentCanActOnObjectsCheckError):
      ChildHandler.validate_class()

  def test_forgot_super_in_can_act_on_objects(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      def can_act_on_objects(self, requested_permission, objects):
        return True

    handler = ChildHandler(services, req)
    with pytest.raises(IncompletePermissionsCheckError):
      handler.prepare()

  def test_forgot_super_in_find_objects(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      def __init__(self, services, request):
        super().__init__(services, request)
        self.object = None

      def find_objects(self):
        return {"object": object()}

      def can_act_on_objects(self, requested_permission, objects):  # pylint: disable=useless-parent-delegation
        return super().can_act_on_objects(requested_permission, objects)

    handler = ChildHandler(services, req)
    with pytest.raises(MissingFoundObjectsError):
      handler.prepare()
    assert handler.object is None

  def test_return_none_in_find_objects(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      def __init__(self, services, request):
        super().__init__(services, request)
        self.object = None

      def find_objects(self):
        return extend_dict(
          super().find_objects(),
          {
            "object": None,
          },
        )

      def can_act_on_objects(self, requested_permission, objects):  # pylint: disable=useless-parent-delegation
        return super().can_act_on_objects(requested_permission, objects)

    handler = ChildHandler(services, req)
    with pytest.raises(InvalidFoundObjectsError):
      handler.prepare()
    assert handler.object is None

  def test_forgot_return_in_find_objects(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      def __init__(self, services, request):
        super().__init__(services, request)
        self.object = None

      def find_objects(self):  # pylint: disable=useless-parent-delegation
        super().find_objects()

      def can_act_on_objects(self, requested_permission, objects):  # pylint: disable=useless-parent-delegation
        return super().can_act_on_objects(requested_permission, objects)

    handler = ChildHandler(services, req)
    with pytest.raises(NoFoundObjectsError):
      handler.prepare()
    assert handler.object is None

  def test_forgot_set_in_init(self, services, req, BaseHandler):
    class ChildHandler(BaseHandler):
      def find_objects(self):
        return extend_dict(
          super().find_objects(),
          {
            "object": OBJECT,
          },
        )

      def can_act_on_objects(self, requested_permission, objects):
        return super().can_act_on_objects(requested_permission, objects) and objects["object"] is OBJECT

    handler = ChildHandler(services, req)
    with pytest.raises(HandlerException):
      handler.prepare()
    assert not hasattr(handler, "object")
