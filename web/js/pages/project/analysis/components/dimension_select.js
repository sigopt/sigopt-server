/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import Select from "react-select";

const optionsFromDims = (dims) =>
  _.map(dims, (dim) => ({label: dim.displayName, value: dim.key}));

export const MultiDimensionSelect = ({dims, selectedDims, setSelectedDims}) => {
  const onChange = React.useCallback(
    (selectedOptions) => setSelectedDims(_.pluck(selectedOptions, "value")),
    [setSelectedDims],
  );

  const options = optionsFromDims(dims);
  const selectedOptions = _.filter(options, (o) =>
    _.contains(selectedDims, o.value),
  );

  return (
    <Select
      styles={{
        menuPortal: (provided) => ({...provided, zIndex: 9999}),
      }}
      menuPortalTarget={document.body}
      options={options}
      isMulti={true}
      closeMenuOnSelect={false}
      value={selectedOptions}
      isClearable={true}
      onChange={onChange}
      placeholder="Select dimension(s)..."
    />
  );
};

export const DimensionSelect = ({dims, selectedDim, setSelectedDim}) => {
  const onChange = React.useCallback(
    (selectedOption) =>
      selectedOption
        ? setSelectedDim(selectedOption.value)
        : setSelectedDim(selectedOption),
    [setSelectedDim],
  );

  const options = optionsFromDims(dims);
  const selectedOption = _.find(options, (o) => selectedDim === o.value);

  return (
    <Select
      styles={{
        menuPortal: (provided) => ({...provided, zIndex: 9999}),
      }}
      menuPortalTarget={document.body}
      options={options}
      isMulti={false}
      closeMenuOnSelect={true}
      value={selectedOption}
      isClearable={true}
      onChange={onChange}
      placeholder="Select a dimension..."
    />
  );
};
