/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

export class SerializeableForClientBundle {
  // This is how the service will be serialized to the client. By default returns nothing
  // so that we do not inadvertently leak anything secret to the user - however if you want
  // your service to be usable clientside you will likely have to include something here
  serializeAs() {
    return {};
  }
}

// Services are individual tools for rendering a component.
// They typically have an `options` object which configures how
// Critically, they are serializeable and deserializeable. This
// ensures that we can send the service configuration over the
// wire and the page will be rendered identically on the client
// and the server.
//
// They also have a reference to all other services. These are not
// serialized (to avoid circular references) but are instead injected
// on creation.
export default class Service extends SerializeableForClientBundle {
  constructor(services, options) {
    super();
    this._services = services;
    this._options = _.extend({}, options);
  }

  get services() {
    return this._services;
  }

  get options() {
    return this._options;
  }
}
