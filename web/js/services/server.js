/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import AjaxClient from "../net/ajax";
import ApiRequestor from "../api/api-requestor";
import ClientsideConfigBroker from "../config/service";
import CollectingAlertBroker from "../server/alert/broker";
import LegacyApiClient from "../api/legacy-api-client";
import NodeRequestor from "../server/net/requestor";
import NoopAlertNotifier from "../server/alert/notify";
import PromiseApiClient from "../api/promise-api-client";
import Service, {SerializeableForClientBundle} from "./base";
import {ServerLoggingService} from "../log/server_logging_service";

export default class ServerServiceBag extends SerializeableForClientBundle {
  serializeAs() {
    return _.chain({}).extend(this).omit("globalServices").value();
  }

  constructor(loginState, traceId, globalServices) {
    super();
    this.globalServices = globalServices;

    const configBroker = globalServices.configBroker;
    this.legacyApiClient = new LegacyApiClient(this);
    this.apiRequestor = new ApiRequestor(this, {
      apiToken: loginState.apiToken,
      apiUrl: configBroker.get("address.internal_api_url"),
      clientApiUrl: configBroker.get("address.api_proxy_url", "/api"),
      traceId: traceId,
    });
    this.alertBroker = new CollectingAlertBroker(this);
    this.errorNotifier = new NoopAlertNotifier(this);
    this.logger = new ServerLoggingService(
      this,
      configBroker.get("logging", {}),
    );
    this.netRequestor = new NodeRequestor(this);
    this.promiseApiClient = new PromiseApiClient(this);

    // TODO(SN-1183): Some services are not applicable serverside, but we still need to
    // thread through their configs. Is there a better way to do this?
    this.ajaxClient = new AjaxClient(this, {csrfToken: loginState.csrfToken});
    this.clientsideConfigBroker = new ClientsideConfigBroker(this, {
      // NOTE: Because many configs are sensitive, we must carefully choose which
      // configs we are okay with sending to the client
      address: {
        api_url: configBroker.get("address.api_proxy_url", "/api"),
        app_url: configBroker.get("address.app_url"),
      },
    });
    this.navigator = new Service(this);
    this.sessionUpdater = new Service(this);
  }
}
