# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import inspect

from zigopt.common import *
from zigopt.api.auth import always_fail_authentication
from zigopt.authorization.constant import AuthorizationDenied
from zigopt.net.errors import ForbiddenError, NotFoundError, RequestError
from zigopt.net.responses import TokenStatus
from zigopt.protobuf.gen.token.tokenmeta_pb2 import ADMIN, NONE, READ, WRITE, TokenMeta
from zigopt.services.api import ApiRequestLocalServiceBag


class HandlerException(Exception):
  pass


class IncompletePermissionsCheckError(HandlerException):
  def __init__(self, handler):
    super().__init__(
      f"Incomplete permissions check in {handler.__class__.__name__},"
      " did you forget to call super().can_act_on_objects()?"
    )


class InconsistentCanActOnObjectsCheckError(HandlerException):
  def __init__(self, cls):
    super().__init__(
      f"`find_objects` is implemented but `can_act_on_objects` is not in {cls.__name__}."
      " We enforce that both of these methods are implemented to prevent accidentally fetching objects in "
      " `find_objects` without a corresponding permission check."
      " Objects fetched in `find_objects` should be checked with an `auth.can_act_on_X` method to make sure"
      " we are never surfacing objects the caller is forbidden from seeing."
      f" Did you forget to implement `can_act_on_objects` in {cls.__name__}?"
    )


class MissingFoundObjectsError(HandlerException):
  def __init__(self, handler):
    super().__init__(
      f"Invalid return value from `find_objects` in {handler.__class__.__name__}"
      " Did you forget to call super().find_objects()?"
    )


class NoFoundObjectsError(HandlerException):
  def __init__(self, handler):
    super().__init__(
      f"No return value from `find_objects` in {handler.__class__.__name__}",
    )


class InvalidInitialValueError(HandlerException):
  def __init__(self, handler, key):
    super().__init__(
      f"Invalid initial value for {key} in `__init__` for {handler.__class__.__name__}, expected None.",
    )


class InvalidFoundObjectsError(HandlerException):
  def __init__(self, handler, key):
    super().__init__(
      f"Expected non-None value returned from `find_objects` for key {key} in {handler.__class__.__name__}"
    )


# Sentinel value for default implementation of find_objects.
# Used to ensure that super() is called within find_objects.
_DEFAULT_FOUND_OBJECT_KEY = "__default_handler_find_objects"
_DEFAULT_FOUND_OBJECT_VALUE = object()


class Handler:
  """
    Base class for API endpoint handlers.
    To implement API endpoints, fill in the methods and class variables to enable the desired functionality.
    The intent is for defaults to be safe, and throw errors if they are not filled in.
    This is instead of providing defaults with the intent of reducing boilerplate or duplicated code.
    This is because it would be quite insidious if there was forgotten permission-checking code,
    since that might not get noticed until it is abused.
    """

  # Allows this endpoint to be accessed with development tokens.
  # By default, endpoints reject calls made with development tokens.
  allow_development = False

  # The types of authentication that are supported. Permitted values include
  #   api_token_authentication - The most common. Any valid API token can be used to call this endpoint.
  #   user_token_authentication - Only API tokens that have user IDs can call this endpoint.
  #   client_token_authentication - Only API tokens that have client IDs can call this endpoint.
  #   no_authentication - This endpoint can be called even without an API token.
  #             This is uncommon and care should be taken to make sure this endpoint is not abused.
  authenticator = always_fail_authentication

  # Permissions that the user must have to access this endpoint.
  # Permissions are NONE < READ < WRITE < ADMIN, each of which has strictly more permissions
  required_permissions = ADMIN

  # Which Token Scopes are able to call this endpoint.
  # If a Token has a Scope other than ALL_ENDPOINTS, by default it will be not able to call any endpoints.
  # Endpoints can indicate that they accept tokens with the designated scope to allow access
  permitted_scopes = tuple([TokenMeta.ALL_ENDPOINTS])

  # Sentinel value for endpoints that take no parameters
  # If this is returned from parse_params, then no argument is provided
  # to the `handler()` method
  NO_PARAMS = object()

  services: ApiRequestLocalServiceBag

  def __init__(self, services, request):
    super().__init__()
    if self.required_permissions not in [NONE, READ, WRITE, ADMIN]:
      raise HandlerException(f"Invalid required_permissions in {self.__class__.__name__}: {self.required_permissions}")

    self._can_act_on_objects_was_called = False
    self.services = services
    self._request = request
    self.auth = None

  # Initial authentication and authorization to call this endpoint.
  # If this method returns successfully, the returned values of `find_objects` will
  # be set on this object, and subsequent code is able to assume that the caller has
  # permission to access those objects.
  # Any exceptions thrown during the lifecyle of this method are sanitized to make sure
  # that we are not inadvertently leaking any information to the user that we should not.
  def prepare(self):
    self.auth = self.authenticator(self.services, self._request)
    self._check_can_access_endpoint()
    objects = self._find_and_authorize_objects(self.required_permissions)
    if not self._can_act_on_objects_was_called:
      raise IncompletePermissionsCheckError(self)
    self._set_objects(objects)

  # This is where the parameters are typically extracted from the request object and validated.
  # The return value of this method is passed to `self.handle`.
  # This is to encourage that parameters are validated up-front,
  # rather than proceeding and potentially making updates before realizing parameters are invalid.
  def parse_params(self, request):
    return Handler.NO_PARAMS

  # This is the main execution logic of the endpoint.
  # The return value of this is serialized and becomes the API response.
  # Provided the return value of `parse_params` as the only parameter, unless `parse_params` returns
  # the default value of NO_PARAMS
  def handle(self):  # type: ignore
    raise NotImplementedError()

  # Fetches objects from the database that will be used in this endpoint.
  # The return value of this is passed to `can_act_on_objects`, for the implementer to make
  # sure that the user has permission to access these objects.
  # The most common calling pattern looks like:
  #   return extend_dict(super().find_objects(), {
  #     'key': self._find_value(...),
  #   })
  # After all validation and authorization is complete, these keys will be set as attributes
  # on this Handler object, so that they can be accessed with `self.key`.
  # This is so that the Handler code can be certain they are not referencing fields on objects
  # before it has been confirmed that the user has authorization
  def find_objects(self):
    return {_DEFAULT_FOUND_OBJECT_KEY: _DEFAULT_FOUND_OBJECT_VALUE}

  # Overridden by handlers and should return True iff `self.auth` is authorized
  # to perform actions of type `requested_permission` on all the objects in `objects`.
  # It is enforced that this method will call `super().can_act_on_objects`.
  # This is to make sure that overridding classes do not inadvertently erase important permission checks.
  # We return True here so that all subclasses can always call `super().can_act_on_objects`
  # While we could return `False` (to encourage all subclasses to override this), it means that
  # direct children would have to skip calling `super` which would be risky.
  # Instead, we will have error-checking code to make sure that `can_act_on_objects` is always
  # implemented wherever `find_objects` is
  def can_act_on_objects(self, requested_permission, objects):
    self._can_act_on_objects_was_called = True
    return True

  def _set_objects(self, objects):
    for key, obj in objects.items():
      if key != _DEFAULT_FOUND_OBJECT_KEY:
        if getattr(self, key, object()) is not None:
          raise InvalidInitialValueError(self, key)
        setattr(self, key, obj)

  def _check_can_access_endpoint(self):
    assert self.auth is not None

    if self.auth.development and not self.allow_development:
      raise ForbiddenError("Development tokens cannot access this endpoint.")
    if self.auth.api_token and self.auth.api_token.scope not in self.permitted_scopes:
      raise ForbiddenError("This token is not permitted to access this endpoint.")

  def _find_and_authorize_objects(self, requested_permission):
    objects = None
    authorization_status = None
    # NOTE: We do not want to leak the existence of objects that
    # the user may not have permission to see, so we are very careful about what we return here.
    # In general, if any error happens before we have verified that the user can READ this object,
    # the returned error should *always* be a 404, to avoid leaking that an object even exists.
    try:
      objects = self.find_objects()
      self._validate_found_objects(objects)
      # TODO: Should this be behind `if requested_permission != NONE`?
      authorization_status = self.can_act_on_objects(requested_permission, objects)
      if not authorization_status:
        raise ForbiddenError()
    except RequestError as e:
      # Try to give a more descriptive error if they are trying to modify something
      # they only have READ permissions on.
      if objects is not None and self.can_act_on_objects(READ, objects):
        raise ForbiddenError(
          (
            "You don't have permission to do this action."
            " You may need to contact your team's administrator to request permissions."
          ),
          token_status=TokenStatus.INVALID_PERMISSIONS,
        ) from e
      if authorization_status is AuthorizationDenied.NEEDS_EMAIL_VERIFICATION:
        raise NotFoundError(
          (
            "The requested resource could not be found."
            " You may need to verify your email before you can make this request."
          ),
          token_status=TokenStatus.NEEDS_EMAIL_VERIFICATION,
        ) from e
      raise NotFoundError() from e
    return objects

  def _validate_found_objects(self, objects):
    if objects is None:
      raise NoFoundObjectsError(self)
    if objects.get(_DEFAULT_FOUND_OBJECT_KEY) is not _DEFAULT_FOUND_OBJECT_VALUE:
      raise MissingFoundObjectsError(self)
    for key, obj in objects.items():
      if obj is None:
        raise InvalidFoundObjectsError(key, self)

  # Checks to make sure that find_objects is always matched with an implementation of can_act_on_objects.
  # If can_act_on_objects is missing, then we assume the developer has forgotten
  # to implement permission checking and throw an error.
  # This is intentionally aggressive - we treat it as a serious error if
  # permission checking is omitted, so we would like to err on the side of false
  # positives for this error checking.
  @classmethod
  def validate_class(cls):
    for parent_cls in inspect.getmro(cls):
      if parent_cls.__dict__.get(cls.find_objects.__name__):
        if not parent_cls.__dict__.get(cls.can_act_on_objects.__name__):
          raise InconsistentCanActOnObjectsCheckError(parent_cls)
