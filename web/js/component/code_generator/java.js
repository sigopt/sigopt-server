/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import {camelCase, upperFirst} from "lodash";

import footerTemplate from "./java_experiment_footer.ms";
import headerTemplate from "./java_experiment.ms";
import {
  ApiCallCodeGen,
  ArrayCodeGen,
  EnclosedBlock,
  INDENT,
  JsonObjectCodeGen,
  KeywordCodeGen,
  PrimitiveCodeGen,
  generateJsonInnerCode,
  makeExperimentCodeGen,
} from "./base";
import {Highlight} from "../code_block";
import {isUndefinedOrNull} from "../../utils";
import {stem, upperCamelCase} from "./utils";

class JavaKeywordCodeGen extends KeywordCodeGen {
  keywords = {
    true: "true",
    false: "false",
    null: "null",
  };
}

class JavaArrayCodeGen extends ArrayCodeGen {
  opener() {
    return "java.util.Arrays.asList(";
  }
  closer() {
    return ")";
  }
}

class JavaJsonSetterCodeGen extends JsonObjectCodeGen {
  opener() {
    if (!this.props.jsonKey) {
      throw new Error("No renderable json key!");
    }
    const key = upperFirst(camelCase(this.props.jsonKey));
    return `new ${key}.Builder()`;
  }
  closer() {
    return ".build()";
  }
  keyOpener(key) {
    return `.set("${key}", `;
  }
  keyCloser() {
    return ")";
  }
  keyJoiner() {
    return "\n";
  }
}

class JavaJsonObjectCodeGen extends JsonObjectCodeGen {
  hasRequiredKeyName() {
    return Boolean(this.getKeyName());
  }

  getKeyName() {
    if (this.props.type) {
      return this.props.type;
    }
    const objName = this.props.codeItem.object;
    if (isUndefinedOrNull(objName)) {
      return null;
    }
    return upperFirst(camelCase(objName));
  }

  opener() {
    return `new ${this.getKeyName()}.Builder()`;
  }
  closer() {
    return ".build()";
  }
  keyOpener(key) {
    return `.${camelCase(key)}(`;
  }
  keyCloser() {
    return ")";
  }
  keyJoiner() {
    return "\n";
  }

  render() {
    if (this.hasRequiredKeyName()) {
      return super.render();
    } else {
      return <JavaJsonSetterCodeGen {...this.props} />;
    }
  }
}

class JavaCategoricalValueJsonCodeGen extends JavaJsonObjectCodeGen {
  opener() {
    return `new ${this.getKeyName()}(`;
  }
  closer() {
    return ")";
  }
  keyOpener() {
    return "";
  }
  keyCloser() {
    return "";
  }
}

class JavaQueryParameters extends JavaJsonObjectCodeGen {
  hasRequiredKeyName() {
    return true;
  }
  opener() {
    return "";
  }
  closer() {
    return "";
  }
  keyOpener(key) {
    return `.addParam("${key}", `;
  }
  keyCloser() {
    return ")";
  }
  keyJoiner() {
    return "\n";
  }
}

class JavaEndpointParameters extends JsonObjectCodeGen {
  render() {
    if (this.props.method === "POST" || this.props.method === "PUT") {
      return [
        <EnclosedBlock key="object" {...this.props} opener=".data(" closer=")">
          {this.props.indent + INDENT}
          <JavaJsonObjectCodeGen
            {...this.props}
            indent={this.props.indent + INDENT}
          />
        </EnclosedBlock>,
      ];
    } else {
      return <JavaQueryParameters {...this.props} indentSize="" />;
    }
  }
}

// TODO: Support batch endpoints
export const JavaApiCodeGenSupportedEndpoint = function (endpoint) {
  return endpoint.path[endpoint.path.length - 1] !== "batch";
};

export class JavaApiCallCodeGen extends ApiCallCodeGen {
  opener() {
    const resource = camelCase(this.props.path[0]);
    const resourceId = this.props.path[1];
    const subresource = camelCase(this.props.path[2]);
    const subresourceId = this.props.path[3];
    const hasId = this.props.path.length % 2 === 0;

    const resourceType = upperCamelCase(stem(resource));
    const leafType = upperCamelCase(stem(subresource || resource));
    const returnType =
      this.props.method === "GET" && !hasId
        ? `Pagination<${leafType}>`
        : leafType;

    const verb = {
      GET: {true: "fetch", false: "list"},
      POST: {true: "create", false: "create"},
      PUT: {true: "update", false: "update"},
      DELETE: {true: "delete", false: "deleteList"},
    }[this.props.method][hasId];

    const declaration =
      this.props.method === "DELETE"
        ? ""
        : `${returnType} ${camelCase(this.props.name)} = `;
    const apiCall = subresource
      ? `new ${resourceType}(${resourceId}).${subresource}(${
          subresourceId || ""
        }).${verb}()`
      : `${resourceType}.${verb}(${resourceId || ""})`;

    return `${declaration}${apiCall}`;
  }
  closer() {
    return ".call();";
  }
  keyOpener(key) {
    return `.${camelCase(key)}(`;
  }
  keyCloser() {
    return ")";
  }
  keyJoiner() {
    return "\n";
  }

  // Including the header necessitates additional indentation
  _baseIndent = () =>
    this.props.indent + (this.props.showHeader ? INDENT + INDENT : "");

  footer() {
    return `\n${this._baseIndent()}return experiment;\n${INDENT}}`;
  }

  render() {
    return (
      <span>
        {this.props.showHeader ? (
          <Highlight
            language={this.props.language}
            code={`${this.props.header(this.props)}\n`}
          />
        ) : null}
        <EnclosedBlock
          {...this.props}
          closer={this.closer()}
          continueLine={true}
          indent={this._baseIndent()}
          opener={this.opener()}
        >
          {!this.isEmptyCodeItem(this.props.codeItem) && (
            <JavaEndpointParameters
              {...this.props}
              indent={this._baseIndent() + INDENT}
            />
          )}
        </EnclosedBlock>
        {this.props.showHeader ? (
          <Highlight language={this.props.language} code={this.footer()} />
        ) : null}
      </span>
    );
  }
}

export const JavaExperimentCodeGen = makeExperimentCodeGen(
  JavaApiCallCodeGen,
  "java",
);

const JAVA_CODE_ITEM_MAPPER = {
  arrayCode: JavaArrayCodeGen,
  jsonCode: JavaJsonObjectCodeGen,
  keywordCode: JavaKeywordCodeGen,
  primitiveCode: PrimitiveCodeGen,
};

const javaGenerateCategoricalValuesInnerCode = function (
  codeItem,
  codeItemMapper,
  indent,
  language,
) {
  return (
    <JavaCategoricalValueJsonCodeGen
      codeItem={codeItem}
      codeItemMapper={codeItemMapper}
      indent={indent}
      language={language}
    />
  );
};

const javaGenerateJsonInnerCode = function (
  key,
  value,
  codeItemMapper,
  indent,
  language,
) {
  const props = {
    codeItem: value,
    codeItemMapper: codeItemMapper,
    indent: indent,
    language: language,
  };
  if (_.contains(["metadata", "conditions"], key)) {
    return <JavaJsonSetterCodeGen jsonKey={key} {...props} />;
  } else if (key === "categorical_values" && _.any(value, _.isObject)) {
    return (
      <JavaArrayCodeGen
        generateInnerCode={javaGenerateCategoricalValuesInnerCode}
        {...props}
      />
    );
  }
  return generateJsonInnerCode(key, value, codeItemMapper, indent, language);
};

JavaArrayCodeGen.defaultProps = _.extend({}, ArrayCodeGen.defaultProps, {
  codeItemMapper: JAVA_CODE_ITEM_MAPPER,
});

JavaJsonObjectCodeGen.defaultProps = _.extend(
  {},
  JsonObjectCodeGen.defaultProps,
  {
    codeItemMapper: JAVA_CODE_ITEM_MAPPER,
    generateInnerCode: javaGenerateJsonInnerCode,
  },
);

JavaApiCallCodeGen.defaultProps = _.extend({}, ApiCallCodeGen.defaultProps, {
  codeItemMapper: JAVA_CODE_ITEM_MAPPER,
  generateInnerCode: javaGenerateJsonInnerCode,
  // HACK: We append the necessary ndentation whitespace at the end of the template file,
  // however it doesn't appear to work. So ensure it exists here
  header: (...args) => `${headerTemplate(...args).trim()}\n    `,
  footer: (...args) => `${footerTemplate(...args).trim()}\n    `,
  indent: "",
});
