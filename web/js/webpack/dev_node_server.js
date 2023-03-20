/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {fork} from "child_process";

const restartPauseMs = 1000;

export default class DevNodeServer {
  constructor(options) {
    this.serverProc = null;
    this.serverBundlePath = options.serverBundlePath;
    this.serverEnv = _.extend({}, process.env, options.env);
  }

  createServerProc() {
    const forkOptions = _.extend(
      {},
      {env: this.serverEnv},
      process.env.SIGOPT_ENABLE_NODE_DEBUG
        ? {execArgv: ["--inspect=0.0.0.0:9229"]}
        : {},
    );
    const serverProc = fork(this.serverBundlePath, forkOptions);
    this.serverProc = serverProc;
    serverProc.on("close", (code) => {
      // eslint-disable-next-line no-console
      console.log(`server process exited with code ${code}`);
      if (this.serverProc === serverProc) {
        this.serverProc = null;
      }
      setTimeout(() => {
        if (!this.serverProc) {
          this.createServerProc();
        }
      }, restartPauseMs);
    });
  }

  apply(compiler) {
    compiler.hooks.afterEmit.tap(this.constructor.name, () => {
      if (this.serverProc) {
        this.serverProc.kill("SIGUSR2");
      } else {
        this.createServerProc();
      }
    });
  }
}
