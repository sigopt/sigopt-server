/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import Section from "../../../component/section";
import {RelativeTime} from "../../../render/format_times";
import {TableCard} from "../../../experiment/tables";

const InfoContent = ({trainingRun, user}) => (
  <TableCard>
    <tbody>
      <tr>
        <td>Run ID</td>
        <td>{trainingRun.id}</td>
      </tr>
      <tr>
        <td>Project ID</td>
        <td>{trainingRun.project}</td>
      </tr>
      <tr>
        <td>Model Type</td>
        <td>{trainingRun.model.type}</td>
      </tr>
      <tr>
        <td>Created</td>
        <td>
          <RelativeTime time={trainingRun.created} />
        </td>
      </tr>
      <tr>
        <td>Creator</td>
        <td>{user ? user.name : "Unknown"}</td>
      </tr>
    </tbody>
  </TableCard>
);

export default (props) => (
  <Section title="Basic Info">
    <InfoContent {...props} />
  </Section>
);
