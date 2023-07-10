/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import ReactDOMServer from "react-dom/server";

import Alert from "../../../alert/alert";
import AppEndpoint from "../../../server/endpoint/app";
import Redirect from "../../../net/redirect";
import Response from "../../../net/response";
import validateContinueHref from "../../../net/continue";
import {APP_URL} from "../../../net/constant";
import {RequestError} from "../../../net/errors";
import {isUndefinedOrNull} from "../../../utils";
import {setLoginStateFromSession} from "../../../session/set";

export default class LoginEndpoint extends AppEndpoint {
  static page = require("./page");

  constructor(status, showNeedsLogin = false) {
    super();
    this.status = status || 200;
    this.showNeedsLogin = showNeedsLogin;
  }

  parseParams(req) {
    if (this.showNeedsLogin && isUndefinedOrNull(req.body)) {
      req.body = {};
    }

    const continueHref = validateContinueHref(
      req.body.continue || req.query.continue,
      req.configBroker,
    );
    const continueLocation = continueHref || "/home";
    const email = req.body.email || req.query.email;
    const password = req.body.password;
    const revoked = req.query.revoked === "1";

    const params = {
      appUrl: req.configBroker.get("address.app_url", APP_URL),
      ajaxClient: this.services.ajaxClient,
      alertBroker: req.services.alertBroker,
      continueHref: continueHref || (this.showNeedsLogin ? req.path : null),
      email: email,
      loginState: req.loginState,
      navigator: this.services.navigator,
      showNeedsLogin: this.showNeedsLogin,
      status: this.status,
    };

    if (req.method === "GET") {
      if (req.currentUser) {
        return Promise.reject(new Redirect(continueLocation));
      } else {
        return Promise.resolve(params);
      }
    } else if (email && password) {
      return this.services.promiseApiClient
        .sessions()
        .create({email: email, password: password})
        .then((session) => this.checkForPreferredClient(session, req))
        .then((session) => this.establishSession(session, req))
        .then((session) =>
          this.determineRedirect(session, req, continueHref, continueLocation),
        )
        .catch((err) => {
          if (err instanceof RequestError) {
            params.status = err.status;
            if (err.status === 400) {
              this.showAlert(
                params,
                <span>
                  Invalid username/password.{" "}
                  <a href="/forgot_password">Forgot your password?</a>
                </span>,
              );
            } else {
              this.showAlert(params, err.message);
            }
            return Promise.resolve(params);
          } else {
            return Promise.reject(err);
          }
        });
    } else {
      let status;
      if (revoked) {
        status = 403;
      } else if (email || password) {
        status = 400;
        this.showAlert(
          params,
          <span>
            Invalid username/password.{" "}
            <a href="/forgot_password">Forgot your password?</a>
          </span>,
        );
      } else {
        status = 200;
        req.forceNewCookieId = true;
      }
      params.status = status;
      return Promise.resolve(params);
    }
  }

  checkForPreferredClient(session, req) {
    if (req.preferences.userId === session.user.id) {
      return this.services.promiseApiClient
        .withApiToken(session.api_token.token)
        .sessions()
        .fetch({preferred_client_id: req.preferences.clientId});
    } else {
      return session;
    }
  }

  establishSession(session, req) {
    setLoginStateFromSession(req.loginState, session);
    req.preferences.setFrom({
      userId: session.user.id,
      clientId: session.client && session.client.id,
    });
    req.forceNewCookieId = true;
    return Promise.resolve(session);
  }

  determineRedirect(session, req, continueHref, continueLocation) {
    if (session.needs_password_reset) {
      const code = session.code;
      const passwordContinueLocation = continueLocation;
      return Promise.reject(
        new Redirect(
          `/change_password?required=1&code=${code}&continue=${passwordContinueLocation}`,
        ),
      );
    } else {
      return Promise.reject(new Redirect(continueLocation));
    }
  }

  showAlert(params, element) {
    const error = new Alert({
      type: "danger",
      __htmlMessage: ReactDOMServer.renderToStaticMarkup(element),
    });
    this.services.alertBroker.handle(error);
    params.error ||= error;
    return params;
  }

  render(params) {
    return new Response(params.status, this.reactElement(params));
  }
}
