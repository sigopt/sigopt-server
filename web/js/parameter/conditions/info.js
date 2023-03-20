/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

const ParameterConditionsInfo = function (props) {
  const conditions = _.chain(props.parameterInput.conditions)
    .pairs()
    .sortBy((pair) => pair[0])
    .value();
  return (
    <div className="parameter-conditions-info">
      <table>
        <tbody>
          {_.map(conditions, ([name, values]) => (
            <tr key={name}>
              <th>{name}</th>
              <td>{`["${_.sortBy(values).join('", "')}"]`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ParameterConditionsInfo;
