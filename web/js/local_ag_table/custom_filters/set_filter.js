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

export default forwardRef((props, ref) => {
  const SELECT_ALL = "selectAll";
  const FILTER_PARAMS_EXISTS = props.colDef.filterParams === undefined;
  const DEFAULT_TO_NOTHING_SELECTED = FILTER_PARAMS_EXISTS
    ? false
    : props.colDef.filterParams.defaultToNothingSelected;

  const getDataAsString = (row, data) => {
    // data can be in a "object.field" format
    const dataList = data.split(".");
    // If data isn't in "object.field" it might still be an object in which case we get the key, otherwse we only need the data
    const dataListLengthOne = () =>
      typeof row[data] === "object"
        ? _.keys(row[data])[0] || ""
        : row[data].toString();
    return dataList.length === 1
      ? dataListLengthOne()
      : row[dataList[0]][dataList[1]] || "";
  };

  const setDataAndCheckList = () => {
    // get rows
    const rowData = props.rowModel.rowsToDisplay.map((row) => row.data);
    const rowDictionary = rowData.map((x) => ({...x}));
    // get all unique values
    const dataList = [
      ...new Set(
        rowDictionary.map((row) => getDataAsString(row, props.colDef.field)),
      ),
    ];
    // initialize checklist with all values set to true
    const initCheckList = Object.assign(
      {},
      ...dataList.map((row) => ({[row]: !DEFAULT_TO_NOTHING_SELECTED})),
    );
    return [dataList, initCheckList];
  };
  const dataAndCheckList = setDataAndCheckList();
  // eslint-disable-next-line react/hook-use-state
  const [allData] = useState(dataAndCheckList[0]);
  const [checkList, setCheckList] = useState(dataAndCheckList[1]);

  const getValuesFromFieldMap = () => {
    return [..._.keys(checkList).map((key) => checkList[key])];
  };

  useImperativeHandle(ref, () => {
    return {
      doesFilterPass(params) {
        return checkList[getDataAsString(params.data, props.colDef.field)];
      },
      isFilterActive() {
        return DEFAULT_TO_NOTHING_SELECTED
          ? _.some(getValuesFromFieldMap())
          : !_.all(getValuesFromFieldMap());
      },
    };
  });

  const onCheckClicked = (event) => {
    let newFieldMap = checkList;
    if (event.target.name === SELECT_ALL) {
      newFieldMap = _.mapObject(checkList, () => event.target.checked);
    } else {
      newFieldMap = _.mapObject(checkList);
      newFieldMap[event.target.name] = event.target.checked;
    }
    setCheckList(newFieldMap);
  };

  useEffect(() => {
    props.filterChangedCallback();
  }, [checkList]);

  return (
    <div className="ag-theme-material" onChange={onCheckClicked}>
      <div className="ag-select-all">
        <input
          name={SELECT_ALL}
          type="checkbox"
          checked={_.all(getValuesFromFieldMap())}
          readOnly={true}
        />
        <span>(select all)</span>
      </div>
      {allData.map((data) => (
        <div className="ag-checkbox" key={data}>
          <input
            name={data}
            checked={checkList[data]}
            type="checkbox"
            readOnly={true}
          />
          <span>{data}</span>
        </div>
      ))}
    </div>
  );
});
