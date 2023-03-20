/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import BookSvg from "../../../../icons/book.svg";
import Icon from "../../../../component/icon";
import SlidersSvg from "../../../../icons/sliders.svg";
import ui from "../../../../experiment/ui";
import {CtaTile} from "../../../../component/cta_tile";
import {DOCS_URL} from "../../../../net/constant";
import {PRODUCT_NAME} from "../../../../brand/constant";

const AddDataPrompt = function (props) {
  return (
    <div className="add-data-prompt">
      <p>To get started, just add some data to this experiment.</p>
      <div className="add-data-options">
        <CtaTile
          header={`${PRODUCT_NAME} Tutorial`}
          href={`${DOCS_URL}/core-module-api-references/quick-start`}
        >
          <Icon imgSrc={BookSvg} />
          <div>
            Learn how {PRODUCT_NAME} works with the Getting Started Tutorial
          </div>
        </CtaTile>
        <CtaTile
          header="Add Data Manually"
          href={ui.getExperimentUrl(props.experiment, {
            aiexperiment: "/inform",
            experiment: "/report",
          })}
        >
          <Icon imgSrc={SlidersSvg} />
          <div>Jump right in and add data with our web interface</div>
        </CtaTile>
      </div>
    </div>
  );
};

export default AddDataPrompt;
