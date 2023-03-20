/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import cookieHandler from "cookie-parser";
import express from "express";
import slashes from "connect-slashes";

import ServerServiceBag from "../../services/server";
import addAlways from "./always";
import addBodyParser from "./body";
import addStaticRoutes from "./static";
import addTimeout from "./timeout";
import checkLoginState from "./check_login_state";
import handleErrors from "./error";
import initializeHealthCheck from "./health";
import initializeRoutes from "./routes";
import logRequests from "./log";
import makeCookieHandlers from "./cookie";
import normalizeMethod from "./normalize_method";
import setApiTokenDetail from "./token";
import setCurrentClient from "./current_client";
import setCurrentExperimentCounts from "./current_experiment";
import setCurrentOrganization from "./current_organization";
import setCurrentUser from "./current_user";
import setMatchedClient from "./client";
import setMatchedExperiment from "./experiment";
import setMatchedOrganization from "./organization";
import setMatchedProject from "./project";
import setMatchedTrainingRun from "./training_run";
import setMatchedUser from "./user";
import setRunFromObservation from "./set_run_from_observation";
import setStandardHeaders from "./headers";
import tooBusy from "./too_busy";
import traceRequests from "./trace";
import validateCsrf from "./csrf";
import {NotFoundError} from "../../net/errors";
import {generateResponse, sendResponse} from "./response";
import {handleRedirects, setRedirect} from "./redirect";

/**
 * Sets a value on the `req` object and continues.
 * Example: set('foo', (req) => 'bar');
 * In the next middleware function, req.foo === 'bar';
 */
const set = function (attr, handler) {
  return (req, res, next) => {
    if (attr in req) {
      next(new Error(`Duplicate set of attribute: ${attr}`));
      return;
    } else {
      req[attr] = handler(req);
      next();
      return;
    }
  };
};

export default function makeApp(globalServices) {
  const configBroker = globalServices.configBroker;
  const {cookieReader, cookieWriter} = makeCookieHandlers(configBroker);

  // Initialize express app
  const app = express();
  addAlways(app);
  app.use(tooBusy);
  app.use(normalizeMethod);

  // Logging and instrumentation
  initializeHealthCheck(app);
  app.use(addTimeout(globalServices));
  app.use(traceRequests());
  app.use(logRequests(globalServices));

  // Request rewriting
  app.use(slashes(false));

  // Proxies to other destinations, so the responses should be unmodified
  addStaticRoutes(configBroker, app);

  // Request preparing middleware - set attributes which should be present on all requests.
  app.use(cookieHandler());
  app.use(cookieReader());

  // Initialize our custom routes
  app.use(set("configBroker", () => configBroker));
  app.use(
    set(
      "services",
      (req) =>
        new ServerServiceBag(req.loginState, req.traceId, globalServices),
    ),
  );
  initializeRoutes(app, configBroker);

  // Set global attributes based on request
  // NOTE: setRedirect() needs to come before checkLoginState() so we redirect before unauthorizing
  app.use(setRedirect());
  app.use(setCurrentUser());
  app.use(checkLoginState());
  app.use(setApiTokenDetail());
  app.use(setCurrentClient());
  app.use(setCurrentExperimentCounts());
  app.use(setCurrentOrganization());
  app.use("/client/:clientId", setMatchedClient());
  app.use("/experiment/:experimentId", setMatchedExperiment());
  app.use("/aiexperiment/:aiExperimentId", setMatchedExperiment());

  app.use(
    "/experiment/:experimentId/observation/:observationId/run",
    setRunFromObservation(),
  );
  app.use(
    "/aiexperiment/:aiExperimentId/observation/:observationId/run",
    setRunFromObservation(),
  );

  app.use("/organization/:organizationId", setMatchedOrganization());
  app.use("/organization/:organizationId/users/:userId", setMatchedUser());
  app.use("/project/:projectId", setMatchedProject());
  app.use("/client/:clientId/project/:projectId", setMatchedProject());
  app.use("/projectruns/:projectId", setMatchedProject());
  app.use("/client/:clientId/projectruns/:projectId", setMatchedProject());
  app.use("/run/:trainingRunId", setMatchedTrainingRun());

  // 404 if there is no matching endpoint at this point
  app.use((req, res, next) =>
    next(req.endpoint ? null : new NotFoundError({path: req.path})),
  );

  // Handle request and generate response
  addBodyParser(app);
  app.use(/\/.*/u, validateCsrf());
  app.use(generateResponse());

  // Finally, send the response to the client
  app.always(setStandardHeaders());
  app.always(cookieWriter());

  // We will send exactly one of the below:
  //   1: A real response. Calling this may induce errors or redirects, so it must come first
  app.use(sendResponse());
  //   2: A redirect response
  app.use(handleRedirects());
  //   3: An error response. This logs the error and sends an error page to the user
  app.use(handleErrors(globalServices));
  return app;
}
