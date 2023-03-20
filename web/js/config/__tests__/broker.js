/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import ConfigBroker from "../broker";
import ObjectSource from "../object";
import {ConfigBrokerValueNotAvailableException} from "../exceptions";
import {NOT_AVAILABLE} from "../constants";

const source1 = new ObjectSource({a: {b: "c", d: "e"}});
const source2 = new ObjectSource({a: {b: "f", y: "z"}});
source1.setNotAvailable("not.available");

describe("ConfigBroker", () => {
  it("fetches from multiple sources", (done) => {
    const broker = new ConfigBroker([source1, source2]);
    broker.initialize(() => {
      expect(broker.get("a.b")).toEqual("c");
      expect(broker.get("a.d")).toEqual("e");
      expect(broker.get("a.y")).toEqual("z");
      expect(() => broker.get("not.available")).toThrow(
        ConfigBrokerValueNotAvailableException,
      );
      expect(() => broker.get("not.available.subkey")).toThrow(
        ConfigBrokerValueNotAvailableException,
      );
      expect(() => broker.getObject("not.available")).toThrow(
        ConfigBrokerValueNotAvailableException,
      );
      expect(() => broker.getObject("not")).toThrow(
        ConfigBrokerValueNotAvailableException,
      );
      expect(broker.getObject("a")).toEqual({
        b: "c",
        d: "e",
        y: "z",
      });
      expect(broker.allConfigsForLogging()).toEqual([
        {
          a: {
            b: "c",
            d: "e",
          },
          not: {
            available: NOT_AVAILABLE,
          },
        },
        {
          a: {
            b: "f",
            y: "z",
          },
        },
      ]);
      done();
    }, done.fail);
  });
});
