/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import BookSvg from "../../../icons/book.svg";
import Icon from "../../../component/icon";
import {DOCS_URL} from "../../../net/constant";
import {PRODUCT_NAME} from "../../../brand/constant";

export default class CoreQuickStartGuide extends React.Component {
  render() {
    return (
      <div className="quick-start-guide container-fluid">
        <div className="quick-start-header">
          <Icon imgSrc={BookSvg} />
          <div className="quick-start-header-text">
            <h2>Quick Start</h2>
            <p>
              You do not have any Core Experiments. Get started with{" "}
              {PRODUCT_NAME} by checking our our{" "}
              <a href={DOCS_URL}>documentation</a>.
            </p>
          </div>
        </div>
      </div>
    );
  }
}
