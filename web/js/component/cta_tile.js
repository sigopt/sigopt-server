/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import classNames from "classnames";

import MaybeLink from "./link";

export const ClickableCtaTile = function (props) {
  const active = props.active ? " active " : "";
  const disabled = props.disabled ? " disabled " : "";

  return (
    <div className="cta-tile-holder">
      <div
        className={classNames("cta-tile", props.className, active, disabled)}
        onClick={props.onClick}
      >
        <div className="header">{props.header}</div>
        <div className="info">{props.children}</div>
      </div>
    </div>
  );
};

export const CtaTile = function (props) {
  const href = props.disabled ? undefined : props.href;

  return (
    <div className="cta-tile-holder">
      <MaybeLink href={href} target={props.target} rel={props.rel}>
        <div
          className={classNames(
            "cta-tile",
            props.active && "active",
            props.disabled && "disabled",
          )}
        >
          <div className="header">{props.header}</div>
          <div className="info">{props.children}</div>
        </div>
      </MaybeLink>
    </div>
  );
};
