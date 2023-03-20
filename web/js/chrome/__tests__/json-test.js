/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import ReactDOMServer from "react-dom/server";

import JsonTag from "../json";

describe("JsonTag", function () {
  it("renders a script tag", function () {
    expect(
      ReactDOMServer.renderToStaticMarkup(
        <JsonTag
          data={{
            a: "b",
            c: 1,
            d: true,
            e: [{}],
          }}
        />,
      ),
    ).toEqual(expect.stringContaining('{"a":"b","c":1,"d":true,"e":[{}]}'));
  });

  it("escapes input", function () {
    const dangerousData = {name: "</script>"};
    const rendered = ReactDOMServer.renderToStaticMarkup(
      <JsonTag data={dangerousData} />,
    );
    const escaped = '{"name":"\\u003c/script>"}';
    expect(rendered).toEqual(expect.stringContaining(`>${escaped}</script>`));
    expect(JSON.parse(escaped)).toEqual(dangerousData);
  });
});
