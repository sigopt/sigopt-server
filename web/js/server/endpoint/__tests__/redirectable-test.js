/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import RedirectableEndpoint from "../redirectable";

describe("RedirectableEndpoint", () => {
  const redirectableEndpoint = new RedirectableEndpoint();

  describe("getUrlRedirectPath", () => {
    const url = "sigopt.ninja";
    const path = "faq";
    const query = {someKey: "someValue"};

    it("creates url without ? when no query", () => {
      const observedPath = redirectableEndpoint.getUrlRedirectPath(
        url,
        path,
        {},
      );
      expect(observedPath).toEqual("sigopt.ninja/faq");
    });

    it("creates url with query string", () => {
      const observedPath = redirectableEndpoint.getUrlRedirectPath(
        url,
        path,
        query,
      );
      expect(observedPath).toEqual("sigopt.ninja/faq?someKey=someValue");
    });
  });
});
