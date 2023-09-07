/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import Spinner from "../component/spinner";

const FullBodyContent = (props) => (
  <tr>
    <td colSpan={100}>{props.children}</td>
  </tr>
);

export default function PagingTableContents(props) {
  const showEmptyState = !props.isPaging && props.isEmpty;

  const spinner = (
    <tbody className="spinner-tbody">
      <FullBodyContent>
        <Spinner position="absolute" />
      </FullBodyContent>
    </tbody>
  );

  const customEmptyState = props.emptyState && (
    <tbody>
      <FullBodyContent>{props.emptyState}</FullBodyContent>
    </tbody>
  );

  // When loading new pages, leave the old content in the footer hidden, so that the table doesn't flicker too much.
  // TODO: How do we get the last seen page?!?! Does props.children work?
  const footer = <tfoot style={{visibility: "hidden"}}>{props.children}</tfoot>;

  const loadedState = (showEmptyState && customEmptyState) || (
    <tbody>{props.children}</tbody>
  );
  const loadingState = (
    <>
      {spinner}
      {footer}
    </>
  );

  return (
    <>
      {props.head}
      {props.data ? loadedState : loadingState}
    </>
  );
}
