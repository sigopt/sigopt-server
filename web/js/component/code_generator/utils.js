/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import {camelCase} from "lodash";

// TODO: More robust name stemming
export const stem = (name) => {
  if (name === "best_assignments") {
    return name;
  }
  return name.charAt(name.length - 1) === "s"
    ? name.substring(0, name.length - 1)
    : name;
};

export const upperCamelCase = (name) => {
  const camelCaseName = camelCase(name);
  return camelCaseName.charAt(0).toUpperCase() + camelCaseName.substring(1);
};
