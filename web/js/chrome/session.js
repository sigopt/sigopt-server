/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import classNames from "classnames";

export default (props) => {
  let identity;
  if (props.currentUser) {
    identity = `${props.currentUser.name} (User ${props.currentUser.id})`;
  } else {
    identity = "someone else";
  }
  return (
    <div
      className={classNames(
        "alert-session",
        props.guestClientToken ? "guest" : null,
      )}
    >
      <div className="text-holder">
        {props.guestClientToken && (
          <>
            <p>You are currently browsing with a guest session.</p>
            {props.guestClientToken.training_run && (
              <p>
                You have read access to{" "}
                <a href={`/run/${props.guestClientToken.training_run}`}>
                  run {props.guestClientToken.training_run}
                </a>
                {""}.
              </p>
            )}
            {props.guestClientToken.experiment && (
              <p>
                You have read access to{" "}
                <a href={`/experiment/${props.guestClientToken.experiment}`}>
                  experiment {props.guestClientToken.experiment}
                </a>
                {""}.
              </p>
            )}
          </>
        )}
        {!props.guestClientToken && (
          <p>You are currently logged in as {identity}</p>
        )}
      </div>
      <div className="btn-holder">
        <form action="/pop_session" className="form tracked" method="post">
          <button type="submit" className="end-session-button">
            End Session
          </button>
          <input name="continue" value="/login" type="hidden" />
          <input name="csrf_token" value={props.csrfToken} type="hidden" />
        </form>
      </div>
    </div>
  );
};
