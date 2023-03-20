/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";
import classNames from "classnames";

export const Section = ({
  infoClassName,
  innerClassName,
  heading,
  sectionMeta,
  sectionBody,
}) => (
  <div className={classNames("info", infoClassName)}>
    <div className="section-heading">{heading}</div>
    {sectionMeta}
    <div
      className={
        innerClassName || "table-responsive experiment-edit-table-holder"
      }
    >
      {sectionBody}
    </div>
  </div>
);
