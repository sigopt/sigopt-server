/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import Tooltip from "../component/tooltip";
import ui from "./ui";
import {DOCS_URL} from "../net/constant";
import {Section} from "./section.js";

const TYPE_TO_SYMBOL = {
  less_than: "<=",
  greater_than: ">=",
};

const LinearConstraintInfo = function (props) {
  const constraint = props.constraint;
  const lhs = _.chain(constraint.terms)
    .reject((term) => term.weight === 0)
    .map((term) =>
      term.weight === 1 ? term.name : `${term.weight} * ${term.name}`,
    )
    .join(" + ")
    .value();
  return `${lhs} ${TYPE_TO_SYMBOL[constraint.type]} ${constraint.threshold}`;
};

const ConstraintsInfo = function (props) {
  return (
    <div className="experiment-constraints">
      <div className="table-responsive experiment-constraints-table-holder">
        <table className="table">
          <tbody>
            {_.map(props.linearConstraints, (linearConstraint, key) => (
              <tr key={key}>
                <td>
                  <LinearConstraintInfo constraint={linearConstraint} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const ConstraintsReadOnlySection = function (props) {
  const hasLinearConstraints = !_.isEmpty(props.linearConstraints);
  return (
    hasLinearConstraints && (
      <Section
        heading={
          <Tooltip
            html={true}
            tooltip={
              <div>
                <a
                  target="_blank"
                  href={`${DOCS_URL}/advanced_experimentation`}
                  rel="noopener noreferrer"
                >
                  Read more and see examples.
                </a>
              </div>
            }
          >
            Constraints
          </Tooltip>
        }
        sectionBody={
          <ConstraintsInfo linearConstraints={props.linearConstraints} />
        }
      />
    )
  );
};

export const ConstraintsSection = function (props) {
  return (
    ui.existingInteraction(props.interactionState) && (
      <ConstraintsReadOnlySection linearConstraints={props.linearConstraints} />
    )
  );
};
