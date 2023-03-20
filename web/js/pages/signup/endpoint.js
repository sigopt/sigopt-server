/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import AppEndpoint from "../../server/endpoint/app";
import Redirect from "../../net/redirect";
import Url from "../../net/url";
import {PRODUCTION_WEB_URL} from "../../net/constant";

export default class SignupEndpoint extends AppEndpoint {
  pageName() {
    return "Sign up";
  }

  static page = require("./page");

  parseParams(req) {
    const code = req.query.code;
    const email = req.query.email;
    const token = req.query.token;
    const isOrgSignup = code || token;
    const allowSelfSignup = req.configBroker.get(
      "features.allowSelfSignup",
      false,
    );
    const allowSignup = isOrgSignup || allowSelfSignup;
    const requireInvite = req.configBroker.get("features.requireInvite", false);
    const isGuest =
      req.apiTokenDetail && req.apiTokenDetail.token_type === "guest";
    const invalidInvite = Boolean(
      !isGuest && code && req.currentUser && req.currentUser.email !== email,
    );

    return this.maybeFetchOrganization(token).then(
      ({client, organization, linkValid}) => {
        const emailVerificationEnabled = req.configBroker.get(
          "email.verify",
          true,
        );
        const unclaimableInvite = Boolean(
          invalidInvite || !linkValid || (!emailVerificationEnabled && token),
        );
        if (req.currentUser && !isGuest && !unclaimableInvite) {
          return this.maybeJoinClient(req, client).then((continueUrl) =>
            Promise.reject(new Redirect(continueUrl || "/")),
          );
        } else if (!requireInvite && !allowSignup) {
          return Promise.reject(
            new Redirect(`${PRODUCTION_WEB_URL}/try-it/enterprise`),
          );
        } else {
          if (token) {
            this.services.apiRequestor.setApiToken(token);
          }
          return {
            alertBroker: this.services.alertBroker,
            appUrl: req.configBroker.get("address.app_url", PRODUCTION_WEB_URL),
            allowSelfSignup,
            client,
            code,
            email,
            hasTokenInUrl: Boolean(token),
            isOrgSignup,
            loginState: req.loginState,
            navigator: this.services.navigator,
            organization,
            promiseApiClient: this.services.promiseApiClient,
            requireInvite,
            sessionUpdater: this.services.sessionUpdater,
            unclaimableInvite,
            verifyPassword: false,
          };
        }
      },
    );
  }

  maybeJoinClient(req, client) {
    if (client) {
      return this.services.promiseApiClient
        .users(req.currentUser.id)
        .permissions()
        .create({client: client.id})
        .then(() => {
          req.loginState.clientId = client.id;
          req.loginState.organizationId = client.organization;
        })
        .then(() => ({newClient: "1"}))
        .catch((err) => {
          if (_.contains([400, 403], err.status)) {
            return Promise.resolve({invalidInvite: "1"});
          } else {
            return Promise.reject(err);
          }
        })
        .then((params) => {
          const url = new Url("/user/info");
          url.params = params;
          return url.toString();
        });
    } else {
      return Promise.resolve("/");
    }
  }

  maybeFetchOrganization(token) {
    const empty = {client: null, organization: null};
    if (token) {
      const promiseApiClient =
        this.services.promiseApiClient.withApiToken(token);
      return promiseApiClient
        .sessions()
        .fetch()
        .then((session) =>
          promiseApiClient
            .organizations(session.client.organization)
            .fetch()
            .then((organization) => ({
              client: session.client,
              organization,
              linkValid: organization.allow_signup_from_email_domains,
            })),
        )
        .catch(() => Promise.resolve(_.extend({linkValid: false}, empty)));
    } else {
      return Promise.resolve(_.extend({linkValid: true}, empty));
    }
  }
}
