/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import Hogan from "hogan.js";

export default function (source) {
  const jsonSrc = JSON.stringify(source);
  const compiled = Hogan.compile(source, {asString: true});
  return [
    `var Template = require("hogan.js").Template;`,
    `module.exports = function() {`,
    `  var template = new Template(${compiled}, ${jsonSrc});`,
    `  return template.render.apply(template, arguments);`,
    `};`,
  ].join("\n");
}
