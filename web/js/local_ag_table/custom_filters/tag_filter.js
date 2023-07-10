/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/components/local_ag_table.less";

import _ from "underscore";
import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useState,
} from "react";

import {TagFilterCell} from "../cell_renderers";

export default forwardRef((props, ref) => {
  const setDataAndCheckList = () => {
    // get rows
    const rowData = props.rowModel.rowsToDisplay.map((row) => row.data);
    // get all unique values
    const dataList = [
      ...new Set(_.flatten([rowData.map((row) => row[props.colDef.field])])),
    ];
    // initialize checklist with all values set to true
    const initCheckList = Object.assign(
      {},
      ...dataList.map((row) => ({[row]: false})),
    );
    return [dataList, initCheckList];
  };
  const dataAndCheckList = setDataAndCheckList();
  // eslint-disable-next-line react/hook-use-state
  const [allData] = useState(dataAndCheckList[0]);
  const [checkList, setCheckList] = useState(dataAndCheckList[1]);

  const getValuesFromFieldMap = () => {
    return [...Object.keys(checkList).map((key) => checkList[key])];
  };

  useImperativeHandle(ref, () => {
    return {
      doesFilterPass(params) {
        let passFilter = true;
        const result = _.mapObject(checkList, (key, value) =>
          checkList[value]
            ? params.data[props.colDef.field].includes(value)
            : true,
        );
        _.mapObject(result, (value) => (passFilter &&= value));
        return passFilter;
      },
      isFilterActive() {
        return _.some(getValuesFromFieldMap());
      },
    };
  });

  const onCheckClicked = (event) => {
    const newFieldMap = _.mapObject(checkList);
    newFieldMap[event.target.name] = event.target.checked;
    setCheckList(newFieldMap);
  };

  useEffect(() => {
    props.filterChangedCallback();
  }, [checkList]);
  return (
    <div className="ag-theme-material" onChange={onCheckClicked}>
      {allData.map((data) => (
        <div className="ag-checkbox" key={data}>
          <input
            name={data}
            checked={checkList[data]}
            type="checkbox"
            readOnly={true}
          />
          <TagFilterCell value={Number(data)} />
        </div>
      ))}
    </div>
  );
});
