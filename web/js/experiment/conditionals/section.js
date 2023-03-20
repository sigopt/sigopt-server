/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import Tooltip from "../../component/tooltip";
import {ConditionalsCreate} from "./input";
import {DOCS_URL} from "../../net/constant";
import {InteractionStates} from "../constants";
import {Section} from "../section.js";

const ConditionalsTooltip = function () {
  return (
    <Tooltip
      html={true}
      tooltip={
        <div>
          (Beta) Conditionals allow you to turn on and off parameters based on
          values.{" "}
          <a
            target="_blank"
            href={`${DOCS_URL}/intro/main-concepts/parameter_space#define-conditional-parameters`}
            rel="noopener noreferrer"
          >
            Read more and see examples.
          </a>
        </div>
      }
    >
      Conditionals
    </Tooltip>
  );
};

const ConditionalsReadOnly = function (props) {
  const conditionals = _.sortBy(
    props.experimentInput.conditionals,
    (c) => c.name,
  );
  return (
    <div className="experiment-conditionals">
      <div className="table-responsive experiment-conditionals-table-holder">
        <table className="table">
          <tbody>
            {_.map(conditionals, (conditional) => (
              <tr key={conditional.name}>
                <th>{conditional.name}</th>
                <td>{`["${_.sortBy(conditional.values).join('", "')}"]`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const ConditionalsCreateSection = function (props) {
  return (
    <ConditionalsCreate
      experimentInput={props.experimentInput}
      onAddConditional={props.onAddConditional}
      onChangeConditional={props.onChangeConditional}
      onRemoveConditional={props.onRemoveConditional}
      setParameter={props.setParameter}
    />
  );
};

export const ConditionalsSection = function (props) {
  const create = props.interactionState === InteractionStates.CREATE;
  const showConditionals =
    create || !_.isEmpty(props.experimentInput.conditionals);

  const conditionalsSection = create ? (
    <ConditionalsCreateSection
      experimentInput={props.experimentInput}
      onAddConditional={props.onAddConditional}
      onChangeConditional={props.onChangeConditional}
      onRemoveConditional={props.onRemoveConditional}
      setParameter={props.setParameter}
    />
  ) : (
    <ConditionalsReadOnly experimentInput={props.experimentInput} />
  );

  return (
    showConditionals && (
      <Section
        heading={<ConditionalsTooltip />}
        sectionBody={conditionalsSection}
      />
    )
  );
};
