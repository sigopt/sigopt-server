/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import URL from "../url";

const parseTestNames = [
  // 'url',
  "scheme",
  "host",
  "port",
  "origin",
  "path",
  "hash",
  "params",
  "resource",
];

const parseTests = [
  ["", "", "", "", "", "", "", {}, ""],
  [
    "http://www.example.com:8080",
    "http",
    "www.example.com",
    "8080",
    "http://www.example.com:8080",
    "/",
    "",
    {},
    "/",
  ],
  [
    "http://example.com/path/to/page.html",
    "http",
    "example.com",
    "",
    "http://example.com",
    "/path/to/page.html",
    "",
    {},
    "/path/to/page.html",
  ],
  [
    "/path/to/page.html#about",
    "",
    "",
    "",
    "",
    "/path/to/page.html",
    "#about",
    {},
    "/path/to/page.html#about",
  ],
  [
    "/path/to/page.html?start=0&end=5&link=https%3A%2F%2Fexternal.com",
    "",
    "",
    "",
    "",
    "/path/to/page.html",
    "",
    {
      start: "0",
      end: "5",
      link: "https://external.com",
    },
    "/path/to/page.html?start=0&end=5&link=https%3A%2F%2Fexternal.com",
  ],
];

const setOriginTests = [
  ["", "https://example.com", "https://example.com"],
  [
    "http://example.com:80/path/to/resource.txt?some=query#anchor",
    "ftp://ftp.example.com:21",
    "ftp://ftp.example.com:21/path/to/resource.txt?some=query#anchor",
  ],
];

describe("url", function () {
  _.each(parseTests, function ([url, ...test]) {
    const parsedUrl = new URL(url);
    _.chain(parseTestNames)
      .zip(test)
      .each(function ([name, value]) {
        it(`parses the ${name} of {${url}}`, function () {
          expect(parsedUrl[name]).toEqual(value);
        });
      });
  });

  _.each(setOriginTests, function ([url, origin, result]) {
    it(`sets origin of {${url}} origin to {${origin}}`, function () {
      const theUrl = new URL(url);
      theUrl.origin = origin;
      expect(theUrl.toString()).toEqual(result);
    });
  });
});
