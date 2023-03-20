/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import BookSvg from "../../../icons/book.svg";
import Icon from "../../../component/icon";
import {ClickableTabs, Tab} from "../../../component/tabs";
import {DOCS_URL} from "../../../net/constant";
import {PRODUCT_NAME} from "../../../brand/constant";
import {
  PythonCreateCodeSection,
  PythonInstallCodeSection,
  PythonOptimizeCodeSection,
} from "../../docs/manuals/lib/get_started/python.js";

export default class AIQuickStartGuide extends React.Component {
  render() {
    return (
      <div className="quick-start-guide container-fluid">
        <div className="quick-start-header">
          <Icon imgSrc={BookSvg} />
          <div className="quick-start-header-text">
            <h2>Quick Start</h2>
            <p>
              You do not have any AI Experiments. Get started with{" "}
              {PRODUCT_NAME} by checking out our{" "}
              <a href={DOCS_URL}>documentation</a> or by following the short
              tutorial below.
            </p>
          </div>
        </div>
        <ClickableTabs className="quick-start-tabs code-example">
          <Tab label="Install">
            <PythonInstallCodeSection {...this.props} />
          </Tab>
          <Tab label="Create">
            <PythonCreateCodeSection {...this.props} />
          </Tab>
          <Tab label="Optimize">
            <PythonOptimizeCodeSection {...this.props} />
          </Tab>
        </ClickableTabs>
      </div>
    );
  }
}
