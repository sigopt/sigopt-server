/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/**
 * Transforms page files to make sure a React component is the
 * default export and that the entrypoint is present.
 */
import fs from "fs";
import hogan from "hogan.js";
import path from "path";

import convertLoader from "./convert_loader";

const templateContent = fs
  .readFileSync(path.resolve(__dirname, "server_side_template.js.ms"))
  .toString("utf8");
const template = hogan.compile(templateContent);

export default convertLoader(function renderEntrypoint(contents, absolutePath) {
  const parsedRelativePath = path.parse(
    path.relative(path.resolve(__dirname, "../pages"), absolutePath),
  );
  const entrypoint = path.join(parsedRelativePath.dir, parsedRelativePath.name);
  return template.render({
    contents,
    entrypoint: JSON.stringify(entrypoint),
  });
});
