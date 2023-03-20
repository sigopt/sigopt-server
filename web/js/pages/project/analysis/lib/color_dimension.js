/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import Select from "react-select";
import natCompare from "natural-compare-lite";

import {DIMENSION_VALUE_TYPES} from "../../data/dimensions";
import {DimensionSelect} from "../components/dimension_select";
import {getDimension} from "./dimensions";
import {isDefinedAndNotNull, isUndefinedOrNull} from "../../../../utils";

export const GRADIENT_TYPES = {
  FIXED: "FIXED",
  SMOOTH: "SMOOTH",
};

// WARNING: These are referenced by key by saved dashboards. Adding stuff is safe, changing/deleting is not.
export const GRADIENTS = {
  [GRADIENT_TYPES.FIXED]: {
    COLOR_BLIND_TEN: {
      // From https://elastic.github.io/eui/#/utilities/color-palettes euiPalleteColorBlind()
      key: "COLOR_BLIND_TEN",
      displayName: "Color Blind Friendly",
      type: GRADIENT_TYPES.FIXED,
      gradient: [
        [0, "#54B399"],
        [0.1, "#D6BF57"],
        [0.2, "#D36086"],
        [0.3, "#9170B8"],
        [0.4, "#CA8EAE"],
        [0.5, "#AA6556"],
        [0.6, "#B9A888"],
        [0.7, "#DA8B45"],
        [0.8, "#6092C0"],
        [0.9, "#E7664C"],
        [1, "#aad9cc"],
      ],
    },
  },
  [GRADIENT_TYPES.SMOOTH]: {
    EVENLY_SPACED: {
      key: "EVENLY_SPACED",
      gradient: [
        [0, "#0098D1"],
        [0.25, "#0B3267"],
        [0.5, "#E7475A"],
        [1, "#F5811F"],
      ],
      type: GRADIENT_TYPES.SMOOTH,
      displayName: "Smooth",
    },
    HIGHLIGHT_HIGH_VALUES: {
      key: "HIGHLIGHT_HIGH_VALUES",
      displayName: "Highlight High Values",
      type: GRADIENT_TYPES.SMOOTH,
      gradient: [
        [0, "#0098D1"],
        [0.9, "#0B3267"],
        [0.99, "#E7475A"],
        [1, "#F5811F"],
      ],
    },
    HIGHLIGHT_LOW_VALUES: {
      key: "HIGHLIGHT_LOW_VALUES",
      displayName: "Highlight Low Values",
      type: GRADIENT_TYPES.SMOOTH,
      gradient: [
        [0, "#F5811F"],
        [0.01, "#E7475A"],
        [0.1, "#0B3267"],
        [1, "#0098D1"],
      ],
    },
  },
};

const arrayToMap = (arr) =>
  _.reduce(
    arr,
    (memo, element) => {
      memo[element] = element;
      return memo;
    },
    {},
  );

export const GRADIENT_KEYS = {
  [GRADIENT_TYPES.FIXED]: arrayToMap(_.keys(GRADIENTS[GRADIENT_TYPES.FIXED])),
  [GRADIENT_TYPES.SMOOTH]: arrayToMap(_.keys(GRADIENTS[GRADIENT_TYPES.SMOOTH])),
};

export const DEFAULT_GRADIENTS = {
  [GRADIENT_TYPES.FIXED]: GRADIENTS[GRADIENT_TYPES.FIXED].COLOR_BLIND_TEN,
  [GRADIENT_TYPES.SMOOTH]: GRADIENTS[GRADIENT_TYPES.SMOOTH].EVENLY_SPACED,
};

const getGradientSafely = (gradientType, gradientKey) => {
  try {
    return GRADIENTS[gradientType][gradientKey];
  } catch (e) {
    /* eslint-disable no-console */
    console.warn(
      `Failed to get gradient of type: ${gradientType} with key: ${gradientKey}. Fell back to defaults`,
    );
    return DEFAULT_GRADIENTS[gradientType];
  }
};

export const createColorState = (key, gradientType, gradientKey) => {
  const validGradient =
    (gradientType === null && gradientKey === null) ||
    Boolean(GRADIENTS[gradientType][gradientKey]);

  if (!validGradient) {
    throw new Error(
      `Gradient with type: ${gradientType}, and key: ${gradientKey} is not valid`,
    );
  }

  return {
    key,
    gradientType,
    gradientKey,
  };
};

export const createBlankColorState = () => createColorState(null, null, null);

export const blue = "#6699ff";
export const orange = "#ffca38";
export const createColorDimensionWithSelect = (
  totalPoints,
  selectedIndexes,
) => {
  const color = _.map(new Array(totalPoints), (unused, i) => {
    if (selectedIndexes.includes(i)) {
      return 1;
    }
    return 0;
  });

  const colorscale = [
    [0, blue],
    [1, orange],
  ];

  return {color, colorscale, showscale: false};
};

export const createColorDimensionSmoothGradient = (colorDim, gradientKey) => {
  const colorscale = getGradientSafely(GRADIENT_TYPES.SMOOTH, gradientKey);

  // Plotly mutates this.... yay.
  const color = colorDim.values.slice();

  return {color, colorscale, showscale: true};
};

// Creates stuff needed for plotly color scales
export const createColorDimensionFixedGradient = (colorDim, gradientKey) => {
  const colorscale = getGradientSafely(
    GRADIENT_TYPES.FIXED,
    gradientKey,
  ).gradient;

  const uniqueVals = _.unique(colorDim.values);
  // TODO What to do if numUnique > colorscale.length? Wraps around for now...
  // Probably want to have dynamically extended colours: https://elastic.github.io/eui/#/utilities/color-palettes

  const color = _.map(colorDim.values, (val) => {
    const safeIndex = _.indexOf(uniqueVals, val) % colorscale.length;
    return colorscale[safeIndex][0];
  });

  const legendItems = _.map(uniqueVals, (uniqVal) => {
    const safeIndex = _.indexOf(uniqueVals, uniqVal) % colorscale.length;
    const itemColor = colorscale[safeIndex][1];

    const value = isDefinedAndNotNull(uniqVal) ? uniqVal : "None";

    return {color: itemColor, value};
  });

  const legendData = {
    title: colorDim.displayName,
    items: legendItems,
  };

  return {color, colorscale, cmin: 0, cmax: 1, legendData};
};

export const createColorDimensionGradient = (dims, colorState) => {
  const colorDimKey = colorState && colorState.key;
  if (!colorDimKey) {
    throw new Error("Missing required `key` property of `colorState`");
  }
  const colorDim = getDimension(dims, colorDimKey);

  if (colorState.gradientType === GRADIENT_TYPES.FIXED) {
    return createColorDimensionFixedGradient(colorDim, colorState.gradientKey);
  } else if (colorState.gradientType === GRADIENT_TYPES.SMOOTH) {
    return createColorDimensionSmoothGradient(colorDim, colorState.gradientKey);
  } else {
    throw new Error(`${colorState.gradientType} is not a valid gradient type.`);
  }
};

export const ColorLegend = ({legendData, flexDirection}) => {
  const sortedItems = legendData.items.sort((a, b) => natCompare(a, b));
  return (
    <div
      style={{
        display: "flex",
        flexDirection,
        width: "100%",
        justifyContent: "center",
        flexWrap: "wrap",
      }}
    >
      <div style={{lineHeight: 1, fontWeight: 700}}> {legendData.title} </div>
      {_.map(sortedItems, (item, index) => (
        <div key={index} style={{display: "flex", marginLeft: 10}}>
          <div
            style={{
              width: 15,
              height: 15,
              top: 55,
              backgroundColor: item.color,
              marginRight: 10,
            }}
          />
          <div style={{lineHeight: 1}}> {item.value} </div>
        </div>
      ))}
    </div>
  );
};

const SigGradientToCssGradient = (sigGradient) => {
  const numSteps = sigGradient.gradient.length;
  const fixedStepAmount = 100 / numSteps;

  const gradientSteps = _.map(sigGradient.gradient, ([step, color], index) => {
    let gradientSpacing = `${(step * 100).toString()}%`;
    if (sigGradient.type === GRADIENT_TYPES.FIXED) {
      const stepStart = fixedStepAmount * index;
      const stepEnd = fixedStepAmount * (index + 1);
      gradientSpacing = `${stepStart}% ${stepEnd}%`;
    }

    return `${color} ${gradientSpacing}`;
  });

  return `linear-gradient(90deg, ${gradientSteps.join(", ")})`;
};

const GradientSelect = ({
  gradientType,
  selectedGradientKey,
  setGradientKey,
}) => {
  const disabled = isUndefinedOrNull(gradientType);
  if (disabled) {
    return (
      <Select
        isClearable={true}
        isDisabled={true}
        placeholder="Select a dimension above first."
      />
    );
  }

  const placeholder = "Select gradient...";

  const options = _.values(
    _.mapObject(GRADIENT_KEYS[gradientType], (key) => ({
      label: GRADIENTS[gradientType][key].displayName,
      value: key,
    })),
  );

  const onChange = React.useCallback(
    (option) => setGradientKey(option && option.value),
    [setGradientKey],
  );
  const value =
    selectedGradientKey &&
    _.find(options, (o) => o.value === selectedGradientKey);

  const gradientPreview = (data) => ({
    alignItems: "center",
    display: "flex",
    justifyContent: "space-between",
    ":after": {
      background: SigGradientToCssGradient(GRADIENTS[gradientType][data.value]),
      content: '" "',
      display: "block",
      marginLeft: 8,
      height: 20,
      flexGrow: 1,
    },
  });

  const customStyles = {
    option: (styles, {data}) => ({...styles, ...gradientPreview(data)}),
    singleValue: (styles, {data}) => ({...styles, ...gradientPreview(data)}),
  };

  return (
    <Select
      isClearable={true}
      isDisabled={disabled}
      value={value}
      options={options}
      onChange={onChange}
      styles={customStyles}
      closeMenuOnSelect={true}
      placeholder={placeholder}
    />
  );
};

export const ColorDimensionPicker = ({dims, colorState, setColorState}) => {
  const [colorDimKey, setColorDimKey] = React.useState(
    colorState && colorState.key,
  );
  const [gradientType, setGradientType] = React.useState(
    colorState && colorState.gradientType,
  );
  const [gradientKey, setGradientKey] = React.useState(
    colorState && colorState.gradientKey,
  );

  React.useEffect(() => {
    if (colorDimKey) {
      const dimension = getDimension(dims, colorDimKey);
      const dimIsNumeric =
        dimension.valueType === DIMENSION_VALUE_TYPES.NUMERIC;
      const dimGradientType = dimIsNumeric
        ? GRADIENT_TYPES.SMOOTH
        : GRADIENT_TYPES.FIXED;
      setGradientType(dimGradientType);
      setGradientKey(DEFAULT_GRADIENTS[dimGradientType].key);
    } else {
      setGradientType(null);
    }
  }, [colorDimKey]);

  React.useEffect(() => {
    if (colorDimKey && gradientType && gradientKey) {
      setColorState(createColorState(colorDimKey, gradientType, gradientKey));
    } else {
      setColorState(null);
    }
  }, [colorDimKey, gradientType, gradientKey]);

  return (
    <div>
      <div>
        <DimensionSelect
          dims={dims}
          selectedDim={colorDimKey}
          setSelectedDim={setColorDimKey}
        />
      </div>
      <div style={{marginTop: 10}}>
        <GradientSelect
          gradientType={gradientType}
          selectedGradientKey={gradientKey}
          setGradientKey={setGradientKey}
        />
      </div>
    </div>
  );
};
