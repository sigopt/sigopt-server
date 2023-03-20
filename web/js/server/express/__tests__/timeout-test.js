/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import EventEmitter from "events";

import addTimeout from "../timeout";

const mockGlobalServices = () => ({
  winstonLogger: {
    logs: [],
    log(err) {
      this.logs.concat(err);
    },
  },
});

describe("addTimeout", function () {
  it("doesnt alert when we dont time out", function (done) {
    const endpoint = {timeout: 0.01};
    const req = new EventEmitter();
    req.endpoint = endpoint;
    req.path = "/experiments";
    const res = new EventEmitter();
    res.finished = false;

    const services = mockGlobalServices();
    const addTimer = addTimeout(services);
    addTimer(req, res, (...args) => {
      expect(args).toHaveLength(0);
    });
    res["__onFinished"]();
    setTimeout(() => {
      expect(services.winstonLogger.logs).toHaveLength(0);
      done();
    }, endpoint.timeout * 2 * 1000);
  });
});
