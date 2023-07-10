/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import ReactDOMServer from "react-dom/server";

import Body from "../../chrome/body";
import Chrome from "../../chrome/chrome";
import ContextProvider from "../../react/context-provider";
import Endpoint from "../endpoint/base";
import Head from "../../chrome/head";
import JsonData from "../../chrome/json";
import LoginState from "../../session/login_state";
import ParameterSerializer from "./parameter";
import Root from "../../chrome/root";
import Serializer from "./base";

export default class DefaultResponseSerializer extends Serializer {
  constructor(parameterSerializer = null) {
    super();
    this._defaultSerializer = new ParameterSerializer();
    this.parameterSerializer = parameterSerializer || this._defaultSerializer;
  }

  getSerializedBody(req, endpointParams, endpointResponse) {
    const services = req.services;
    const configBroker = req.configBroker;
    const endpoint = req.endpoint || new Endpoint();
    const loginState = new LoginState(req.loginState || {}).toJson();
    const canPopSession = Boolean(req.loginState && req.loginState.parentState);
    const guestClientToken =
      req.apiTokenDetail && req.apiTokenDetail.token_type === "guest"
        ? req.apiTokenDetail
        : null;

    const cssFiles = [];
    const jsFiles = [];
    if (endpoint.entrypoint) {
      const entryAssets = services.globalServices.entryManifest.getAssets(
        endpoint.entrypoint,
      );
      _.each(entryAssets.css, (cssUrl) =>
        cssFiles.push({
          href: cssUrl,
          rel: "stylesheet",
        }),
      );
      _.each(entryAssets.js, (jsUrl) =>
        jsFiles.push({
          crossOrigin: "anonymous",
          src: jsUrl,
        }),
      );
    }

    const pageName = endpoint.pageName(req);

    const chromeArgs = _.extend(
      {
        alerts: _.map(services.alertBroker.getAlerts(), (a) => a.toJson()),
        canPopSession: canPopSession,
        csrfToken: loginState.csrfToken,
        currentClient: req.currentClient,
        currentOrganization: req.currentOrganization,
        currentUser: req.currentUser,
        currentUserPermissions: req.currentUserPermissions,
        currentUserMemberships: req.currentUserMemberships,
        guestClientToken: guestClientToken,
        loginState: loginState,
        pageRenderTime: new Date().getTime() / 1000,
        pageName,
        path: req.path,
        reactStrictMode: endpoint.reactStrictMode,
        status: endpointResponse.status,
        showSidebarNav: endpoint.showSidebarNav(),
        experimentCount: req.experimentCount,
        aiExperimentCount: req.aiExperimentCount,
      },
      endpoint.baseTemplateParams,
    );

    const body = endpointResponse.body;

    return `<!DOCTYPE html>${ReactDOMServer.renderToStaticMarkup(
      <Root>
        <Head
          cssFiles={cssFiles}
          forbidSearchEngineIndex={configBroker.get(
            "web.forbidSearchEngineIndex",
            false,
          )}
          includeJs={!endpoint.omitJs}
          pageName={endpoint.pageName(req)}
          pageNamePrefix={
            endpoint.pageNamePrefix ? endpoint.pageNamePrefix(req) : null
          }
        />
        <Body
          csrfToken={loginState.csrfToken}
          currentUser={req.currentUser}
          includeJs={!endpoint.omitJs}
          jsFiles={jsFiles}
        >
          <div
            className="chrome-content"
            dangerouslySetInnerHTML={{
              __html: ReactDOMServer.renderToString(
                <ContextProvider
                  loginState={loginState}
                  services={services}
                  pageRenderTime={chromeArgs.pageRenderTime}
                >
                  <Chrome {...chromeArgs} content={body} />
                </ContextProvider>,
              ),
            }}
          />
          <JsonData
            id="chrome-args"
            data={this._defaultSerializer.serialize(chromeArgs)}
          />
          <JsonData
            id="page-args"
            data={this.parameterSerializer.serialize(endpointParams || {})}
          />
          <JsonData
            id="service-args"
            data={this._defaultSerializer.serialize(services)}
          />
        </Body>
      </Root>,
    )}`;
  }

  serialize(req, res, endpointParams, endpointResponse) {
    const body = this.getSerializedBody(req, endpointParams, endpointResponse);
    res.send(body);
  }
}
