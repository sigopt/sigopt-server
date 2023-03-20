/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import AjaxClient from "../net/ajax";
import AlertBroker from "../alert/broker";
import ApiRequestor from "../api/api-requestor";
import ClientLoggingService from "../log/client_logging_service";
// TODO(SN-1181): Is it possible for this to only `require` the services
// we need to render the page? Not a big deal right now since these are
// pretty small, and needed on just about every page
import ClientsideConfigBroker from "../config/service";
import ErrorNotifier from "../alert/notify";
import JqueryRequestor from "../net/requestor";
import LegacyApiClient from "../api/legacy-api-client";
import Navigator from "../net/navigator";
import PromiseApiClient from "../api/promise-api-client";
import SessionUpdater from "../net/session";

export default class ClientServiceBag {
  constructor(serviceArgs) {
    // NOTE: globalServices are only available serverside since they
    // are long-lived (with significant warmup costs) and typically are not appropriate
    // to be executed clientside.
    // If code that references globalServices makes it to the client, that's probably
    // an error.
    // TODO(SN-1182): We should figure out a way to enforce this more robustly
    this.globalServices = null;

    this.ajaxClient = new AjaxClient(this, serviceArgs.ajaxClient);
    this.legacyApiClient = new LegacyApiClient(
      this,
      serviceArgs.legacyApiClient,
    );
    this.apiRequestor = new ApiRequestor(this, serviceArgs.apiRequestor);
    this.alertBroker = new AlertBroker(this);
    this.clientsideConfigBroker = new ClientsideConfigBroker(
      this,
      serviceArgs.clientsideConfigBroker,
    );
    this.errorNotifier = new ErrorNotifier(this);
    this.logger = new ClientLoggingService(this, serviceArgs.logger);
    this.navigator = new Navigator(this);
    this.netRequestor = new JqueryRequestor(this);
    this.promiseApiClient = new PromiseApiClient(this);
    this.sessionUpdater = new SessionUpdater(this);
  }
}
