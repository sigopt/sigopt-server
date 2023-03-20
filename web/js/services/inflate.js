/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

// Given a JSON object (that was sent back from the server), fill in the services
// Turns {ajaxClient: {}, foo: bar} into {ajaxClient: new AjaxClient(), foo: bar};
export default function inflateServices(params, services) {
  const prunedServices = _.pick(services, _.keys(params));
  return _.extend({}, params, prunedServices);
}
