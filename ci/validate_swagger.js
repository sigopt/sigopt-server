#!/usr/bin/node
/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

const fs = require("fs");
const SwaggerParser = require("@apidevtools/swagger-parser");

const myArgs = process.argv.slice(2);
let path = "./artifacts/swagger.json";
if (myArgs.length > 0) {
  path = myArgs[0];
}

/* eslint-disable-next-line no-console */
console.log("About to validate swag file %s", path);

try {
  if (fs.existsSync(path)) {
    const rawData = fs.readFileSync(path);
    const apiSpec = JSON.parse(rawData);
    SwaggerParser.validate(apiSpec, (err, api) => {
      if (err) {
        /* eslint-disable-next-line no-console */
        console.error(err);
        /* eslint-disable-next-line no-console */
        console.error(JSON.stringify(apiSpec, null, "\t"));
        process.exit(1);
      } else {
        /* eslint-disable-next-line no-console */
        console.log("Validation passed for API %s", api.info.title);
        process.exit(0);
      }
    });
  } else {
    /* eslint-disable-next-line no-console */
    console.error("No file found %s", path);
    process.exit(1);
  }
} catch (err) {
  /* eslint-disable-next-line no-console */
  console.error(err);
  process.exit(1);
}
