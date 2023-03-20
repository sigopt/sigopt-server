/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/**
 * Transforms page files so that they are fit to be sent to the client.
 * A page file is is any file in web/js/pages/ that
 *  - is named `page.js` OR
 *  - has the extension `.page.js`.
 * Page files must have single, default export.
 * This default export must be a renderable React component.
 * The component will receive props from an endpoint.
 */
import fs from "fs";
import hogan from "hogan.js";
import path from "path";

import convertLoader from "./convert_loader";

const templateContent = fs
  .readFileSync(path.resolve(__dirname, "entrypoint_template.js.ms"))
  .toString("utf8");
const template = hogan.compile(templateContent);

export default convertLoader(function renderEntrypoint(contents) {
  return template.render({contents});
});
