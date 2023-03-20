/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

export default function MaybeLink(props) {
  // See https://mathiasbynens.github.io/rel-noopener
  const target = props.target;
  const rel =
    props.rel || (props.target === "_blank" ? "noopener noreferrer" : null);
  return props.href ? (
    <a target={target} rel={rel} {..._.omit(props, "target", "rel")}>
      {props.children}
    </a>
  ) : (
    <span className={props.className}>{props.children}</span>
  );
}
