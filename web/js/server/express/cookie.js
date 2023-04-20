/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import {
  DeleteObjectCommand,
  GetObjectCommand,
  PutObjectCommand,
  S3Client,
} from "@aws-sdk/client-s3";

import LoginState from "../../session/login_state";
import Preferences from "../user_prefs";
import {
  cookieExpiryInSeconds,
  isValidCookieId,
  newRandomCookieId,
} from "../cookie/utils";
import {newCsrfToken} from "../csrf";

// const SAME_SITE = "Strict";
const LAX = "Lax";

const readFromS3 = (s3, cookiejarBucket, cookieId) => {
  return s3.send(
    new GetObjectCommand({
      Bucket: cookiejarBucket,
      Key: cookieId,
    }),
  );
};

const writeToS3 = (s3, cookiejarBucket, cookieId, cookieData) => {
  return s3.send(
    new PutObjectCommand({
      Bucket: cookiejarBucket,
      Key: cookieId,
      Body: cookieData,
    }),
  );
};

const deleteFromS3 = (s3, cookiejarBucket, cookieId) => {
  return s3
    .send(
      new DeleteObjectCommand({
        Bucket: cookiejarBucket,
        Key: cookieId,
      }),
    )
    .catch((err) =>
      // eslint-disable-next-line no-console
      console.error(`Error deleting cookie ${cookieId} from s3: ${err}`),
    );
};

const readCookieFromCookiejar = (s3, cookiejarBucket, cookieId) => {
  return readFromS3(s3, cookiejarBucket, cookieId)
    .then(({Body}) => Body.transformToString())
    .then(
      (bodyStr) => {
        try {
          return JSON.parse(bodyStr);
        } catch (e) {
          // eslint-disable-next-line no-console
          console.error(`Could not parse corrupt cookie: ${bodyStr}`);
          return {};
        }
      },
      (err) => {
        if (err?.name === "NoSuchKey") {
          return {};
        }
        throw err;
      },
    );
};

const putCookieInCookiejar = (s3, cookiejarBucket, cookieId, cookieState) => {
  return writeToS3(s3, cookiejarBucket, cookieId, JSON.stringify(cookieState));
};

const removeCookieFromCookiejar = (s3, cookiejarBucket, cookieId) => {
  return deleteFromS3(s3, cookiejarBucket, cookieId);
};

export const readRequestCookies = function (s3, cookiejarBucket, cookieName) {
  return (req, res, next) => {
    let cookieId = req.cookies[cookieName];
    let cookieJarP = Promise.resolve([{}, null]);
    if (isValidCookieId(cookieId)) {
      cookieJarP = readCookieFromCookiejar(s3, cookiejarBucket, cookieId).then(
        (cookieState) => [cookieState || {}, cookieState ? cookieId : null],
      );
    } else {
      cookieId = null;
    }
    return cookieJarP
      .then(([cookieState, newCookieId]) => {
        req.loginState = new LoginState(
          cookieState.loginState || {csrfToken: newCsrfToken()},
        );
        req.preferences = new Preferences(cookieState.preferences);
        req.cookieState = cookieState;
        req.cookieId = newCookieId;
        next();
      })
      .catch(next);
  };
};

export const setResponseCookies = function (
  s3,
  cookiejarBucket,
  cookieName,
  disableCookiesKey,
  cookieSpec,
) {
  return (req, res, next) => {
    const cookieState = {
      loginState: req.loginState?.toJson?.(),
      preferences: req.preferences?.json,
    };
    let cookieId = req.cookieId;
    if (!cookieId || req.forceNewCookieId) {
      cookieId = newRandomCookieId();
    }
    let cookiejarP;
    if (req.cookieId === cookieId && _.isEqual(cookieState, req.cookieState)) {
      cookiejarP = Promise.resolve(null);
    } else {
      cookiejarP = putCookieInCookiejar(
        s3,
        cookiejarBucket,
        cookieId,
        cookieState,
      );
    }
    if (isValidCookieId(req.cookieId) && req.cookieId !== cookieId) {
      cookiejarP = Promise.all([
        cookiejarP,
        removeCookieFromCookiejar(s3, cookiejarBucket, req.cookieId),
      ]);
    }
    return cookiejarP
      .then(() => {
        res.cookie(cookieName, cookieId, cookieSpec);
        return next();
      })
      .catch(next);
  };
};

export default function makeCookieHandlers(configBroker) {
  const cookieName = configBroker.get("web.cookie_name", "sigopt-session-id");
  const s3Options = {};
  const cookiejarRegion = configBroker.get("web.cookiejar_region", null);
  if (cookiejarRegion) {
    s3Options.region = cookiejarRegion;
  }
  const cookiejarEndpoint = configBroker.get("web.cookiejar_endpoint", null);
  if (cookiejarEndpoint) {
    s3Options.endpoint = cookiejarEndpoint;
  }
  const cookiejarCredentials = configBroker.get(
    "web.cookiejar_credentials",
    null,
  );
  if (cookiejarCredentials) {
    s3Options.credentials = cookiejarCredentials;
  }
  s3Options.forcePathStyle = configBroker.get(
    "web.cookiejar_force_path_style",
    false,
  );
  const s3 = new S3Client(s3Options);
  const cookieSpec = {
    // NOTE: including domain forces browsers to add leading dot, extending cookies to subdomains
    // but, explicitly adding leading dot breaks localhost (doesn't store any cookie at all)
    encode: (v) => v,
    httpOnly: true,
    maxAge: cookieExpiryInSeconds(configBroker),
    sameSite: LAX,
  };
  const cookiejarBucket = configBroker.get("web.cookiejar_bucket");
  const cookieReader = () =>
    readRequestCookies(s3, cookiejarBucket, cookieName);
  const cookieWriter = () =>
    setResponseCookies(s3, cookiejarBucket, cookieName, cookieSpec);
  return {cookieReader, cookieWriter};
}
