/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import ReactDOMServer from "react-dom/server";

import {AbsoluteTime} from "../format_times.js";

describe("AbsoluteTime", function () {
  it("formats times correctly", () => {
    const timestamp = 1609795080;
    const readableFormatted = "Jan 4 2021, 9:18 PM";
    const preciseFormatted = "Jan 4 2021, 21:18:00";
    const rendered = `<span title="${preciseFormatted}" data-reactroot="">${readableFormatted}</span>`;
    expect(
      ReactDOMServer.renderToString(<AbsoluteTime time={timestamp} />),
    ).toEqual(rendered);
  });
});
