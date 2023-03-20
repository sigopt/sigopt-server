/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {isValidElementType} from "react-is";

const UNIT_TESTING = process.env.NODE_ENV === "unit-testing";

const checkLoaderApplied = (pageExports) => {
  if (UNIT_TESTING) {
    // NOTE: jest does not apply the custom server-side page loader
    // so we skip this check for unit testing
    return;
  }
  if (!pageExports["__page__"]) {
    throw new Error(
      "The page is not correctly referenced by the endpoint." +
        ' The endpoint should have a static page defined as `static page = require("./path/to/page");`' +
        " Pages should be named `page.js` or end with `.page.js`",
    );
  }
};

const checkCorrectExportKeys = (pageExports) => {
  const expectedKeys = ["default"];
  if (!UNIT_TESTING) {
    // NOTE: the server-side page loader adds these keys to the exports
    expectedKeys.push("entrypoint");
    expectedKeys.push("__page__");
  }
  if (!_.isEqual(_.keys(pageExports), expectedKeys)) {
    throw new Error(
      `The page web/js/pages/${pageExports.entrypoint}.js must only have a single default export`,
    );
  }
};

const checkDefaultReactComponent = (pageExports) => {
  if (!isValidElementType(pageExports.default)) {
    throw new Error(
      `Default export for page web/js/pages/${pageExports.entrypoint}.js is not a valid Component`,
    );
  }
};

export default function checkPageExports(pageExports) {
  checkLoaderApplied(pageExports);
  checkCorrectExportKeys(pageExports);
  checkDefaultReactComponent(pageExports);
}
