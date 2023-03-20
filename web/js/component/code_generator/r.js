/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import headerTemplate from "./r_experiment.ms";
import {
  ApiCallCodeGen,
  ArrayCodeGen,
  JsonObjectCodeGen,
  KeywordCodeGen,
  PrimitiveCodeGen,
  generateJsonInnerCode,
  makeExperimentCodeGen,
} from "./base";

const rGenerateJsonInnerCode = function (
  key,
  value,
  codeItemMapper,
  indent,
  language,
) {
  let codeItem = value;
  if (key === "categorical_values") {
    codeItem = _.map(codeItem, (c) => c.name);
  }
  return generateJsonInnerCode(key, codeItem, codeItemMapper, indent, language);
};

class RKeywordCodeGen extends KeywordCodeGen {
  keywords = {
    true: "TRUE",
    false: "FALSE",
    null: "NULL",
  };
}

class RArrayCodeGen extends ArrayCodeGen {
  opener() {
    return "list(";
  }
  closer() {
    return ")";
  }
}

class RJsonObjectCodeGen extends JsonObjectCodeGen {
  opener() {
    return "list(";
  }
  closer() {
    return ")";
  }
  keyOpener(key) {
    return `${key} = `;
  }
  keyCloser() {
    return "";
  }
}

// TODO(SN-1153): Support other api calls
class RApiCallCodeGen extends ApiCallCodeGen {
  opener() {
    return "experiment <- create_experiment(list(";
  }
  closer() {
    return "))";
  }
  keyOpener(key) {
    return `${key} = `;
  }
  keyCloser() {
    return "";
  }
}

export const RExperimentCodeGen = makeExperimentCodeGen(RApiCallCodeGen, "r");

const R_CODE_ITEM_MAPPER = {
  arrayCode: RArrayCodeGen,
  jsonCode: RJsonObjectCodeGen,
  keywordCode: RKeywordCodeGen,
  primitiveCode: PrimitiveCodeGen,
};

RArrayCodeGen.defaultProps = _.extend({}, ArrayCodeGen.defaultProps, {
  codeItemMapper: R_CODE_ITEM_MAPPER,
});

RJsonObjectCodeGen.defaultProps = _.extend({}, JsonObjectCodeGen.defaultProps, {
  codeItemMapper: R_CODE_ITEM_MAPPER,
  generateInnerCode: rGenerateJsonInnerCode,
});

RApiCallCodeGen.defaultProps = _.extend({}, ApiCallCodeGen.defaultProps, {
  codeItemMapper: R_CODE_ITEM_MAPPER,
  header: headerTemplate,
});
