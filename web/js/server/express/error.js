/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import ReactDOMServer from "react-dom/server";

import ErrorEndpoint from "../../pages/error/endpoint";
import LoginEndpoint from "../../pages/landing/login/endpoint";

const errorPageResponse = (req, err) => {
  const status = err.status || 500;

  const ConfigLoginEndpoint = LoginEndpoint;
  const endpoint = err.showNeedsLogin
    ? new ConfigLoginEndpoint(status, err.showNeedsLogin)
    : new ErrorEndpoint(status, err);
  endpoint.services = req.services;
  req.endpoint = endpoint;
  return endpoint.getParams(req).then((endpointParams) => {
    req.endpointParams = endpointParams;
    req.endpointResponse = endpoint.render(endpointParams);
    return endpoint
      .serializer()
      .getSerializedBody(req, req.endpointParams, req.endpointResponse);
  });
};

// A stack trace response. Express can do this, but by default it kills the server and has to restart,
// which is annoying in dev
const stackTraceResponse = (req, err) =>
  Promise.resolve(
    ReactDOMServer.renderToStaticMarkup(
      <html>
        {/* This h1 disambiguates our custom error page from the express native error page */}
        <h1>{err.message || "Something has gone wrong!"}</h1>
        <body>
          <pre>{err && err.stack}</pre>
        </body>
      </html>,
    ),
  );

export const logError = (req, err) => {
  /* eslint-disable no-console */
  return Promise.resolve()
    .then(() => {
      if (req.services) {
        req.services.logger.error("sigopt.www.apiexception", err);
      } else {
        console.error(err);
      }
    })
    .catch((loggingError) => {
      console.error(err);
      console.error(loggingError);
    });
  /* eslint-enable no-console */
};

export const errorHandler = (initialError, req, res, globalServices) =>
  Promise.resolve(initialError)
    .then((errorToLog) =>
      logError(req, errorToLog)
        .catch((loggingError) => Promise.resolve(loggingError))
        .then(() => Promise.resolve(errorToLog)),
    )
    .then((errorToRender) =>
      Promise.resolve()
        .then(() => {
          const showTrace =
            !errorToRender.showNeedsLogin &&
            globalServices.configBroker.get(
              "web.show_exception_trace",
              false,
            ) &&
            req.path !== "/nsickness" &&
            process.env.NODE_ENV !== "production";
          return showTrace
            ? stackTraceResponse(req, errorToRender)
            : errorPageResponse(req, errorToRender);
        })
        .then((response) => {
          res.status(errorToRender.status || 500);
          res.send(response);
        }),
    )
    .catch((renderError) => logError(req, renderError));

export default function handleErrors(globalServices) {
  return (err, req, res, next) => {
    errorHandler(err, req, res, globalServices).then(
      () => next(),
      // At this point, if there's an error in the error handling then it's too late
      // to do anything. We've already tried to render, log, and report the error
      // above so there's nothing left to do
      (/* unknownErr */) => next(),
    );
  };
}
