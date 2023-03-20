/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

/**
 * Used for a vertical section of the page which extends across the full width of the window
 *
 * For example:
 * <div>
 *   <PageSection>
 *     <h1>title goes here</h1>
 *     <p>Summary info</p>
 *   </PageSection>
 *   <PageSection>
 *     <p>More info goes here</p>
 *   </PageSection>
 * </div>
 *
 * Commonly, PageSections will have different background colors to separate them visually
 */
export default function PageSection(props) {
  return (
    <section className={props.className}>
      <div className={props.fluid ? "container-fluid" : "container"}>
        {props.children}
      </div>
    </section>
  );
}
