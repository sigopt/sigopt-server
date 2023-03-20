/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import AngleDownGlyph from "../../../component/glyph/angle-down";
import Table from "./table";
import sortObject from "./sort_object";

const TableGroup = ({title, items, headers, isOpen}) => {
  const [showTable, setShowTable] = React.useState(isOpen);
  const glyphClassName = showTable ? "table-opened" : "table-closed";

  return (
    <div>
      <div
        className="table-header-row"
        onClick={() => setShowTable(!showTable)}
      >
        <h4 className="subtitle">{title}</h4>
        <div className="caret-section">
          <AngleDownGlyph className={glyphClassName} />
        </div>
      </div>
      {showTable && (
        <Table
          headers={headers}
          content={sortObject(items)}
          copyObject={items}
        />
      )}
    </div>
  );
};

export const ComplexTable = ({groups, headers}) => {
  return (
    <div className="complex-table">
      {_.map(groups, (group) => (
        <TableGroup
          headers={headers}
          title={group.title}
          items={group.items}
          isOpen={group.defaultOpen}
        />
      ))}
    </div>
  );
};
