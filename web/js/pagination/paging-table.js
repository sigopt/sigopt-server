/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import PagingTableContents from "./paging-table-contents";

export default function PagingTable(props) {
  return (
    <table className={props.className}>
      <PagingTableContents {...props} />
    </table>
  );
}
