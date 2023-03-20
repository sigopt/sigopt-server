# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
import html
import itertools
import json
import os
from urllib.parse import urlparse

import pytest
import requests
from lxml import html as lhtml
from requests.cookies import RequestsCookieJar

from zigopt.common import *
from zigopt.membership.model import MembershipType

from integration.base import BaseTest
from integration.connection import IntegrationTestConnection
from integration.utils.html import validate_html


class WebResponse(object):
  def __init__(self, requests_response):
    self.response = requests_response
    content_type = self.response.headers["content-type"]
    assert content_type
    self.html = "text/html" in content_type
    # HACK: We return html5, but xpath doesn't appear to work on the parsed html5.
    # So we serialize it back as html4 and then reparse
    self._parsed = lhtml.fromstring(lhtml.tostring(validate_html(self.response_text()))) if self.html else None
    if self._parsed is not None:
      self._validate_links()

  @property
  def status_code(self):
    return self.response.status_code

  @property
  def redirect_url(self):
    if 300 <= self.status_code < 400:
      return self.response.headers["location"]
    if self.response.history:
      redirect = self.response.history[0]
      return redirect.headers["location"]
    return None

  def get_csrf_token(self):
    return self.xpath('//div[@class="csrf-token"]/text()')[0] if self.html else None

  def xpath(self, xpath):
    return self._parsed.xpath(xpath)

  def response_text(self):
    return self.response.text

  def body_html(self):
    return lhtml.tostring(self._parsed.xpath("//body")[0], encoding="unicode")

  def content_html(self):
    return lhtml.tostring(self._parsed.xpath('//div[@class="content"]')[0], encoding="unicode")

  def page_title(self):
    if self._parsed is not None:
      return self._parsed.xpath("//title/text()")[0]
    return None

  def _validate_links(self):
    links = self.xpath("//a/@href")
    local_links, external_links = partition(links, lambda l: l.startswith("/") or l.startswith("."))
    assert local_links
    for link in local_links:
      if link.startswith("/"):
        Routes.check_valid_route(link)
      else:
        assert link.startswith(".")
        raise NotImplementedError(f"Relative links not implemented: {link}")
    for link in external_links:
      prefixes = ["http://", "https://", "mailto:", "#"]
      if not any(link.startswith(prefix) for prefix in prefixes):
        raise Exception(f"{link!r} does not have a valid prefix {prefixes!r}")

  def __contains__(self, value):
    return html.escape(value, quote=False) in self.content_html()


class WebConnection(object):
  def __init__(self, app_url, email=None, password=None):
    self.app_url = app_url
    self.routes = Routes(self.app_url)
    self.email = email
    self.password = password
    self.csrf_token = None
    self._session = requests.Session()
    self.reset()

  def reset(self):
    self._session = requests.Session()
    self.csrf_token = None
    # Populate session / csrf_token
    self.get("/")

  def get_browser_cookies(self, config_broker):
    netloc = urlparse(self.app_url).netloc
    domain = netloc.split(":", 1)[0]
    browser_cookies = []
    for cookie_name, cookie_value in self.cookies.items():
      full_domain = domain
      sigopt_cookie = config_broker.get("web.scoped_cookie_name", "sigopt-session-id")
      is_local = "localhost" in domain or "127.0.0.1" in domain
      if not is_local and cookie_name == sigopt_cookie:

        full_domain = "." + domain
      browser_cookies.append(
        {
          "name": cookie_name,
          "value": cookie_value,
          "path": "/",
          "domain": full_domain,
        }
      )
    return browser_cookies

  @property
  def cookies(self):
    return self._session.cookies

  def copy_cookies_from(self, cookies):
    assert isinstance(cookies, RequestsCookieJar)
    jar = RequestsCookieJar()
    jar.update(cookies)
    self._session.cookies = jar

  def login(self):
    return self.login_as(self.email, self.password)

  def login_as(self, email, password):
    return self.post(
      "/login",
      {
        "email": email,
        "password": password,
      },
    )

  def get(self, url, params=None, raise_for_status=True, **kwargs):
    if not url.startswith("http"):
      url = self.routes.get_url_base(url) + url
    return self._handle_response(self._request("get", url, params=params, **kwargs), raise_for_status)

  def _request(self, method, path, **kwargs):
    # HACK: use SIGOPT_API_VERIFY_SSL_CERTS only if this is a sigopt hostname
    request_options = dict(kwargs)
    netloc = urlparse(path).netloc
    if "sigopt." in netloc:
      request_options.setdefault("verify", os.environ.get("SIGOPT_API_VERIFY_SSL_CERTS", True))
    # POST redirects are followed by browsers as GETs
    # also manually handle redirects for TLS
    parsed_base = urlparse(path)
    real_allow_redirects = kwargs.get("allow_redirects")
    request_options["allow_redirects"] = False
    resp = self._session.request(method, path, **request_options)
    if resp.is_redirect and real_allow_redirects is not False:
      if resp.headers["location"].startswith("https://docs.sigopt.com"):
        return resp
      location = resp.headers["location"]
      if not urlparse(location).netloc:
        location = parsed_base.scheme + "://" + parsed_base.netloc + location
      next_resp = self._request("get", location, **kwargs)
      next_resp.history = [resp] + resp.history
      return next_resp
    else:
      return resp

  def post(self, url, data=None, hide_csrf=False, raise_for_status=True, **kwargs):
    data = data or {}
    if isinstance(data, dict):
      data = extend_dict({}, data, self.post_data(hide_csrf))
    return self._handle_response(
      self._request("post", self.routes.get_url_base(url) + url, data=data, **kwargs), raise_for_status
    )

  def post_data(self, hide_csrf):
    return {} if hide_csrf else {"csrf_token": self.csrf_token}

  def post_file(self, url, data, filename, **kwargs):
    return self._handle_response(
      self._request(
        "post",
        self.routes.get_url_base(url) + url,
        data=self.post_data(hide_csrf=False),
        files={filename: data},
        **kwargs,
      ),
      raise_for_status=True,
    )

  def _handle_response(self, response, raise_for_status):
    if raise_for_status:
      response.raise_for_status()
    web_response = WebResponse(response)
    if web_response.page_title() == "Leaving Hosted Site - SigOpt":
      pytest.skip()
    self.csrf_token = web_response.get_csrf_token() or self.csrf_token
    return web_response


class ApiConnection(object):
  def __init__(self, sigopt_connection, client_id, user_id, organization_id=None):
    if client_id is not None and organization_id is None:
      raise Exception("client_id provided without orgainzation_id")
    self.conn = sigopt_connection
    self.client_id = client_id
    self.organization_id = organization_id
    self.user_id = user_id

  def __getattr__(self, name):
    return getattr(self.conn, name)


class LoginState(object):
  def __init__(self, email, password, user_id, user_token, client_id, organization_id, client_token):
    self.email = email
    self.password = password
    self.user_id = user_id
    self.user_token = user_token
    self.client_id = client_id
    self.organization_id = organization_id
    self.client_token = client_token


_routes = None


def load_routes():
  global _routes
  if _routes is None:
    try:
      with open("artifacts/web/routes/routes.json") as routes_fp:
        _routes = json.load(routes_fp)
    except FileNotFoundError as fne:
      raise Exception(
        "Could not find route definitions."
        " The route definitions are used in web and browser tests"
        " to check that links are valid and generate test cases."
        " They are generated from the web code by running ./scripts/compile/generate_routes"
      ) from fne
  return _routes


def _app_routes():
  app_routes = load_routes()["app"]
  assert app_routes
  return app_routes


def _static_routes():
  static_routes = load_routes()["static"]
  assert static_routes
  return [r + ("/:rest*" if r.endswith("/:folder") else "") for r in static_routes]


class Routes(object):
  APP_ROUTES = _app_routes()
  STATIC_ROUTES = _static_routes()
  ALL_ROUTES = APP_ROUTES + STATIC_ROUTES

  def __init__(self, app_url):
    self.app_url = app_url

  @classmethod
  def _matches_route(cls, link, route):
    link = urlparse(link).path
    link_parts = link.rstrip("/").split("/")[1:]
    route_parts = route.rstrip("/").split("/")[1:]
    for link_part, route_part in itertools.zip_longest(link_parts, route_parts):
      if route_part is None:
        return False
      if route_part.startswith(":") and route_part.endswith("*"):
        return True
      if link_part != route_part and not route_part.startswith(":"):
        return False
    return True

  @classmethod
  def _is_valid_route(cls, url, routes):
    return any(cls._matches_route(url, r) for r in routes)

  @classmethod
  def _check_valid_route(cls, url, routes):
    if not cls._is_valid_route(url, routes):
      raise Exception(f"{url!r} does not match any valid route {routes!r}")

  @classmethod
  def check_valid_route(cls, url):
    return cls._check_valid_route(url, cls.ALL_ROUTES)

  def get_url_base(self, url):
    return self.app_url

  def get_full_url(self, url):
    if url.startswith("/"):
      return f"{self.get_url_base(url)}{url}"
    return url


class WebBase(BaseTest):
  @classmethod
  @pytest.fixture(scope="function")
  def login_state(cls, auth_provider):
    return cls.make_login_state(auth_provider)

  @classmethod
  def make_login_state(cls, auth_provider, has_verified_email=True, is_owner=True, email=None):
    email = email or auth_provider.randomly_generated_email()
    password = auth_provider.randomly_generated_password()
    user_id, user_token = auth_provider.create_user_tokens(
      email=email,
      password=password,
      has_verified_email=has_verified_email,
    )
    client_id, client_token, organization_id = auth_provider.create_client_tokens(
      user_id=user_id,
      membership_type=MembershipType.owner if is_owner else MembershipType.member,
    )
    return LoginState(email, password, user_id, user_token, client_id, organization_id, client_token)

  @classmethod
  @pytest.fixture(scope="function")
  def api_connection(cls, config_broker, api, login_state):
    return cls.make_api_connection(config_broker, api, login_state)

  @classmethod
  def make_api_connection(cls, config_broker, api, login_state):
    api_url = cls.get_api_url(config_broker)
    return ApiConnection(
      IntegrationTestConnection(
        api_url=api_url,
        api=api,
        client_token=login_state.client_token,
        user_token=login_state.user_token,
      ),
      client_id=login_state.client_id,
      user_id=login_state.user_id,
      organization_id=login_state.organization_id,
    )

  @classmethod
  @pytest.fixture(scope="function")
  def development_api_connection(cls, api_connection, api, config_broker, login_state):
    return cls.make_development_connection(api_connection, api, config_broker, login_state)

  @classmethod
  def make_development_connection(cls, api_connection, api, config_broker, login_state):
    api_url = cls.get_api_url(config_broker)
    development_token = find(
      api_connection.clients(api_connection.client_id).tokens().fetch().data, lambda t: t.development
    )
    return ApiConnection(
      IntegrationTestConnection(
        api_url,
        api=api,
        client_token=development_token.token,
      ),
      client_id=login_state.client_id,
      user_id=login_state.user_id,
      organization_id=login_state.organization_id,
    )

  @classmethod
  def make_admin_api_connection(cls, config_broker, api, user_token):
    api_url = cls.get_api_url(config_broker)
    conn = IntegrationTestConnection(api_url, api, user_token=user_token)
    user_id = conn.sessions().fetch().user.id
    return ApiConnection(conn, client_id=None, user_id=user_id, organization_id=None)

  @classmethod
  @pytest.fixture(scope="function")
  def admin_api_connection(cls, config_broker, api, auth_provider):
    user_token = auth_provider.get_admin_user_token()
    return cls.make_admin_api_connection(config_broker, api, user_token)

  @classmethod
  def make_web_connection(cls, config_broker):
    app_url = cls.get_app_url(config_broker)
    return WebConnection(app_url=app_url)

  @classmethod
  @pytest.fixture
  def web_connection(cls, config_broker, web):
    del web
    return cls.make_web_connection(config_broker)

  @classmethod
  def make_logged_in_web_connection(cls, config_broker, login_state):
    app_url = cls.get_app_url(config_broker)
    conn = WebConnection(app_url=app_url, email=login_state.email, password=login_state.password)
    conn.login_as(login_state.email, login_state.password)
    return conn

  @classmethod
  @pytest.fixture
  def logged_in_web_connection(cls, config_broker, login_state, web):
    del web
    return cls.make_logged_in_web_connection(config_broker, login_state)

  @classmethod
  @pytest.fixture(params=["in", "out"])
  def any_connection(cls, request, web_connection, logged_in_web_connection):
    if request.param == "in":
      return logged_in_web_connection
    return web_connection
