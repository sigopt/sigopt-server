/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import classNames from "classnames";

export const VerticalTableField = ({content, dataKey, label}) => (
  <tr data-key={dataKey}>
    <th>{label}</th>
    <td>{content}</td>
  </tr>
);
VerticalTableField.displayName = "VerticalTableField";

export const VerticalTableBodyWrapper = ({children}) => (
  <tbody>{children}</tbody>
);
VerticalTableBodyWrapper.displayName = "VerticalTableBodyWrapper";

export const VerticalTableSection = function VerticalTableSection(props) {
  return (
    <VerticalTableBodyWrapper>
      {_.map(props.item, ([label, content, key], index) => (
        <VerticalTableField
          dataKey={key || index}
          key={label}
          label={label}
          content={content}
        />
      ))}
    </VerticalTableBodyWrapper>
  );
};

export const VerticalTableWrapper = ({children, className}) => (
  <div
    className={classNames(
      "table-responsive vertical-table-holder experiment-table-holder",
      className,
    )}
  >
    <table className="table table-condensed">{children}</table>
  </div>
);
VerticalTableWrapper.displayName = "VerticalTableWrapper";

export const VerticalTable = function VerticalTable(props) {
  const data = props.getFormattedData(props.items);
  return (
    <VerticalTableWrapper>
      {_.map(data, (item, index) => (
        <VerticalTableSection key={index} item={item} />
      ))}
    </VerticalTableWrapper>
  );
};
