/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../styles/less/libs/base.less";

import React from "react";
import classNames from "classnames";

import PageSection from "./page_section";

/**
 * A PageSection that is styled as the body content for a page.
 */
export default function PageBody(props) {
  return (
    <PageSection
      className={classNames("page-body", props.className)}
      fluid={true} // TODO(SN-1046): remove fluid after merge with new-page-navie
    >
      <div className="row">
        <div className="page-body-content">{props.children}</div>
      </div>
    </PageSection>
  );
}
