/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import CircleQuestionGlyph from "../../component/glyph/circle-question";
import CustomTooltip from "../../component/custom_tooltip";
import {DOCS_URL} from "../../net/constant";

class StagnationInfo extends React.Component {
  static propTypes = {
    stoppingCriteria: PropTypes.object,
  };

  render() {
    const possibleStagnationEncountered =
      this.props.stoppingCriteria &&
      this.props.stoppingCriteria.reasons &&
      this.props.stoppingCriteria.reasons.indexOf("possible_stagnation") >= 0;

    return (
      <div className="chart-detail-section">
        {possibleStagnationEncountered ? (
          <CustomTooltip
            tooltip={[
              "We have detected possible stagnation in your experiment",
              " since no improvement has been observed for a while. ",
              <a
                key="1"
                href={`${DOCS_URL}/core-module-api-references/api-objects/stopping-criteria-object`}
              >
                Learn more about Stopping Criteria here.
              </a>,
            ]}
            html={true}
          >
            <i>Possible stagnation encountered</i>
            <span className="tooltip-trigger">
              <CircleQuestionGlyph />
            </span>
          </CustomTooltip>
        ) : null}
      </div>
    );
  }
}

export default StagnationInfo;
