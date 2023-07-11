/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import PageBody from "./page_body";
import PageTitle from "./page_title";

/**
 * An easy-to-use wrapper for setting up a Page with a consistent style. Includes
 *
 * a) A consistently styled title
 * b) Standard styles depending on if this is a logged-in or logged-out page
 * c) A styled page body
 *
 * This wrapper will handle all the bootstrap container/row/column nesting for you, so you
 * shouldn't need to add any of those styles manually, unless you want to nest your own
 * column layout.
 */
export default function Page(props) {
  const className = _.compact([
    props.loggedIn && "logged-in-page",
    props.className,
  ]).join(" ");

  return (
    <div id={props.id} className={className}>
      {props.title ? <PageTitle title={props.title} /> : null}
      <PageBody>{props.children}</PageBody>
    </div>
  );
}
