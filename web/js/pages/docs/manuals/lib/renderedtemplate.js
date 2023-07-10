/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import {APP_URL} from "../../../../net/constant";

export default (template, props) => {
  const args = _.omit(props, "template");
  if (args.apiToken) {
    args.apiToken = `"${args.apiToken}"`;
  } else {
    args.apiToken = "SIGOPT_API_TOKEN";
  }
  args.projectId ||= "sigopt-examples";
  args.projectId = `"${args.projectId}"`;
  if (!args.appUrl) {
    args.appUrl = APP_URL;
  }
  return template(args);
};
