/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import setFromUrlMatch from "./match";
import {NotFoundError, PromptForLoginError} from "../../net/errors";

export default function setMatchedProject() {
  return setFromUrlMatch(
    (req, s, e) => {
      const clientId = req.params.clientId || req.loginState.clientId;
      if (clientId) {
        return req.services.promiseApiClient
          .clients(clientId)
          .projects(req.params.projectId)
          .fetch()
          .then(s, e);
      } else if (req.loginState.userId) {
        return e(new NotFoundError());
      } else {
        return e(new PromptForLoginError());
      }
    },
    (req, project) => {
      req.matchedProject = project;
    },
  );
}
