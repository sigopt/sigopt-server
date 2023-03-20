/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import {TableCard} from "../../../experiment/tables";

export default ({content, copyObject, headers}) => (
  <TableCard copyObject={copyObject}>
    {_.isEmpty(headers) ? null : (
      <thead>
        <tr>
          {_.map(headers, (header, j) => (
            <th key={j}>{header}</th>
          ))}
        </tr>
      </thead>
    )}
    <tbody>
      {_.map(content, (items, i) => (
        <tr key={i}>
          {_.map(items, (item, j) => (
            <td key={j}>{item}</td>
          ))}
        </tr>
      ))}
    </tbody>
  </TableCard>
);
