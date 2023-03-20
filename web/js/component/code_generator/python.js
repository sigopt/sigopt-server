/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";

import footerTemplate from "./python_experiment_footer.ms";
import headerTemplate from "./python_experiment.ms";
import {
  ApiCallCodeGen,
  ArrayCodeGen,
  JsonObjectCodeGen,
  KeywordCodeGen,
  PrimitiveCodeGen,
  generateJsonInnerCode,
  makeExperimentCodeGen,
} from "./base";

const pythonGenerateJsonInnerCode = function (
  key,
  value,
  codeItemMapper,
  indent,
  language,
) {
  let codeItem = value;
  if (key === "categorical_values" && _.isObject(value)) {
    codeItem = _.map(codeItem, (c) => c.name);
  }
  return generateJsonInnerCode(key, codeItem, codeItemMapper, indent, language);
};

class PythonKeywordCodeGen extends KeywordCodeGen {
  keywords = {
    true: "True",
    false: "False",
    null: "None",
  };
}

class PythonArrayCodeGen extends ArrayCodeGen {
  opener() {
    return "[";
  }
  closer() {
    return "]";
  }
}

class PythonJsonObjectCodeGen extends JsonObjectCodeGen {
  opener() {
    return "dict(";
  }
  closer() {
    return ")";
  }
  keyOpener(key) {
    return `${key}=`;
  }
  keyCloser() {
    return "";
  }
}

class PythonApiCallCodeGen extends ApiCallCodeGen {
  opener() {
    let apiCall = "";
    const path = this.props.path;
    const isBatch = path[path.length - 1] === "batch";
    for (let i = 0; i < path.length; i += 2) {
      const domain = path[i];
      const maybeId = path[i + 1] || "";
      const id = maybeId === "batch" ? "" : maybeId;
      apiCall += `.${domain}(${id})`;
    }
    const verb = {
      GET: {default: "fetch"},
      POST: {batch: "create_batch", default: "create"},
      PUT: {default: "update"},
      DELETE: {default: "delete"},
    }[this.props.method][isBatch ? "batch" : "default"];
    return `${this.props.name} = conn${apiCall}.${verb}(`;
  }
  closer() {
    return ")";
  }
  keyOpener(key) {
    return `${key}=`;
  }
  keyCloser() {
    return "";
  }
}

export const PythonExperimentCodeGen = makeExperimentCodeGen(
  PythonApiCallCodeGen,
  "python",
);

const PYTHON_CODE_ITEM_MAPPER = {
  arrayCode: PythonArrayCodeGen,
  jsonCode: PythonJsonObjectCodeGen,
  keywordCode: PythonKeywordCodeGen,
  primitiveCode: PrimitiveCodeGen,
};

PythonArrayCodeGen.defaultProps = _.extend({}, ArrayCodeGen.defaultProps, {
  codeItemMapper: PYTHON_CODE_ITEM_MAPPER,
});

PythonJsonObjectCodeGen.defaultProps = _.extend(
  {},
  JsonObjectCodeGen.defaultProps,
  {
    codeItemMapper: PYTHON_CODE_ITEM_MAPPER,
    generateInnerCode: pythonGenerateJsonInnerCode,
  },
);

PythonApiCallCodeGen.defaultProps = _.extend({}, ApiCallCodeGen.defaultProps, {
  codeItemMapper: PYTHON_CODE_ITEM_MAPPER,
  header: headerTemplate,
  footer: footerTemplate,
});
