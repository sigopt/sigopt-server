/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "./style.less";

import React from "react";

export const BreadcrumbContainer = ({children}) => (
  <div className="breadcrumb-container">{children}</div>
);

export const Breadcrumb = ({href, label}) => (
  <span className="sig-breadcrumb">
    <a href={href}>
      <span className="link-label">{label}</span>
    </a>
  </span>
);
