/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import Alert from "../alert";

describe("Alert", () => {
  _.each(
    [
      {},
      {type: "danger", message: "abc"},
      {type: "success", __htmlMessage: "<span>def</span>"},
    ],
    (a) => {
      it("can be constructed from itself", () => {
        expect(a).toEqual(new Alert(a).toJson());
        const a1 = new Alert(a);
        const a2 = new Alert(a);
        expect(a1.type).toEqual(a2.type);
        expect(a1.message).toEqual(a2.message);
        expect(a1["__htmlMessage"]).toEqual(a2["__htmlMessage"]);
        expect(a1.toJson()).toEqual(a2.toJson());
      });
    },
  );
});
