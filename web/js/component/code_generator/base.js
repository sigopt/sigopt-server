/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import {APP_URL} from "../../net/constant";
import {Highlight} from "../code_block";
import {isJsObject, isUndefinedOrNull} from "../../utils";

const INDENT = "  ";
export const JSON_OBJECT_DENY_LIST = ["created", "id", "object", "updated"];

const LANGUAGE_PROP_TYPE = PropTypes.oneOf(["python", "r"]).isRequired;

const CODE_ITEM_MAPPER_SHAPE = PropTypes.shape({
  arrayCode: PropTypes.func,
  jsonCode: PropTypes.func,
  keywordCode: PropTypes.func,
  primitiveCode: PropTypes.func,
});

class CodeItemGenerator extends React.Component {
  static propTypes = {
    codeItem: PropTypes.oneOfType([
      PropTypes.array,
      PropTypes.object,
      PropTypes.symbol,
      PropTypes.bool,
      PropTypes.node,
    ]).isRequired,
    codeItemMapper: CODE_ITEM_MAPPER_SHAPE.isRequired,
  };

  render() {
    const codeItem = this.props.codeItem;
    const mapper = this.props.codeItemMapper;

    if (_.isArray(codeItem)) {
      return <mapper.arrayCode {...this.props} />;
    } else if (_.isBoolean(codeItem) || isUndefinedOrNull(codeItem)) {
      return <mapper.keywordCode {...this.props} />;
    } else if (isJsObject(codeItem)) {
      return <mapper.jsonCode {...this.props} />;
    }
    return <mapper.primitiveCode {...this.props} />;
  }
}

export class PrimitiveCodeGen extends React.Component {
  static propTypes = {
    codeItem: PropTypes.node.isRequired,
    language: LANGUAGE_PROP_TYPE,
  };

  render() {
    return (
      <Highlight
        language={this.props.language}
        code={JSON.stringify(this.props.codeItem)}
      />
    );
  }
}

export class KeywordCodeGen extends React.Component {
  static propTypes = {
    codeItem: PropTypes.oneOfType([PropTypes.symbol, PropTypes.bool])
      .isRequired,
    language: LANGUAGE_PROP_TYPE,
  };

  keywords = {
    true: "true",
    false: "false",
    null: "null",
  };

  render() {
    return (
      <Highlight
        language={this.props.language}
        code={this.keywords[this.props.codeItem]}
      />
    );
  }
}

class EnclosedBlock extends React.Component {
  static defaultProps = {
    indentSize: INDENT,
  };

  render() {
    const hasChildren = !_.isEmpty(React.Children.toArray(this.props.children));
    if (hasChildren) {
      const opener = this.props.opener && (
        <Highlight key="opener" {...this.props} code={this.props.opener} />
      );
      const closer = this.props.closer && (
        <Highlight key="closer" {...this.props} code={this.props.closer} />
      );
      return [
        !this.props.continueLine && this.props.indent,
        opener,
        opener && "\n",
        // TODO: Should probably be a React.cloneElement here to increase indent on the children...
        this.props.children,
        closer && "\n",
        this.props.indent + this.props.indentSize,
        closer,
      ];
    } else {
      return (
        <Highlight
          key="closer"
          language={this.props.language}
          code={`${this.props.opener}${this.props.closer}`}
        />
      );
    }
  }
}

export class ArrayCodeGen extends React.Component {
  static propTypes = {
    codeItem: PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.object,
        PropTypes.array,
      ]),
    ).isRequired,
    codeItemMapper: CODE_ITEM_MAPPER_SHAPE.isRequired,
    generateInnerCode: PropTypes.func.isRequired,
    indent: PropTypes.string.isRequired,
    indentSize: PropTypes.string.isRequired,
    language: LANGUAGE_PROP_TYPE,
  };

  opener() {
    return "list(";
  }
  closer() {
    return ")";
  }
  itemJoiner() {
    return ",\n";
  }

  render() {
    const nextIndent = `${this.props.indent}${this.props.indentSize}`;
    const innerCode = _.chain(this.props.codeItem)
      .map((item) => [
        nextIndent,
        this.props.generateInnerCode(
          item,
          this.props.codeItemMapper,
          nextIndent,
          this.props.language,
        ),
        this.itemJoiner(),
      ])
      .flatten()
      .initial()
      .value();
    return (
      <EnclosedBlock
        {...this.props}
        continueLine={true}
        opener={this.opener()}
        closer={this.closer()}
      >
        {_.map(innerCode, (code, key) => (
          <span key={key}>{code}</span>
        ))}
      </EnclosedBlock>
    );
  }
}

export class JsonObjectCodeGen extends React.Component {
  static propTypes = {
    codeItem: PropTypes.object.isRequired,
    codeItemMapper: CODE_ITEM_MAPPER_SHAPE.isRequired,
    denyList: PropTypes.arrayOf(PropTypes.string).isRequired,
    generateInnerCode: PropTypes.func.isRequired,
    indent: PropTypes.string.isRequired,
    indentSize: PropTypes.string.isRequired,
    language: LANGUAGE_PROP_TYPE,
  };

  opener() {
    return "{";
  }
  closer() {
    return "}";
  }
  keyOpener(key) {
    return `"${key}": `;
  }
  keyCloser() {
    return "";
  }
  keyJoiner() {
    return ",\n";
  }

  sanitizedCodeItem(codeItem) {
    return _.omit(codeItem, this.props.denyList);
  }

  isEmptyCodeItem(codeItem) {
    return _.isEmpty(this.sanitizedCodeItem(codeItem));
  }

  schwartzianMap(item) {
    const key = item[0];
    return {
      sortKey: _.contains(["name", "parameters", "min"], key) ? 0 : 1,
      key: key,
      value: item[1],
    };
  }

  render() {
    const nextIndent = `${this.props.indent}${this.props.indentSize}`;
    const innerCode = _.chain(this.sanitizedCodeItem(this.props.codeItem))
      .pairs()
      .map(this.schwartzianMap)
      .sortBy("key")
      .sortBy("sortKey")
      .map((d) => [
        nextIndent,
        <Highlight
          key={d.key}
          language={this.props.language}
          code={this.keyOpener(d.key)}
        />,
        this.props.generateInnerCode(
          d.key,
          d.value,
          this.props.codeItemMapper,
          nextIndent,
          this.props.language,
        ),
        this.keyCloser(),
        this.keyJoiner(),
      ])
      .flatten()
      .initial()
      .value();
    return (
      <EnclosedBlock
        {...this.props}
        continueLine={true}
        opener={this.opener()}
        closer={this.closer()}
      >
        {_.map(innerCode, (code, key) => (
          <span key={key}>{code}</span>
        ))}
      </EnclosedBlock>
    );
  }
}

export class ApiCallCodeGen extends JsonObjectCodeGen {
  static propTypes = {
    apiToken: PropTypes.string,
    apiUrl: PropTypes.string,
    appUrl: PropTypes.string,
    footer: PropTypes.func,
    header: PropTypes.func,
    language: LANGUAGE_PROP_TYPE,
    method: PropTypes.oneOf(["GET", "POST", "PUT", "DELETE"]).isRequired,
    path: PropTypes.arrayOf(PropTypes.string).isRequired,
    showHeader: PropTypes.bool.isRequired,
    type: PropTypes.string,
  };

  render() {
    const templateArgs = {
      apiToken: this.props.apiToken,
      apiUrl: this.props.apiUrl,
      appUrl: this.props.appUrl || APP_URL,
    };
    return (
      <span>
        {this.props.showHeader && this.props.header ? (
          <Highlight
            language={this.props.language}
            code={`${this.props.header(templateArgs)}\n`}
          />
        ) : null}
        {super.render()}
        {"\n"}
        {this.props.showFooter && this.props.footer ? (
          <Highlight
            language={this.props.language}
            code={this.props.footer(templateArgs)}
          />
        ) : null}
      </span>
    );
  }
}

export const EXPERIMENT_DENY_LIST = _.union(JSON_OBJECT_DENY_LIST, [
  "client",
  "deleted",
  "metric",
  "object",
  "progress",
  "state",
  "user",
  "development",
  "enum_index",
]);

export const makeExperimentCodeGen = (BaseApiCallCodeGen, language) =>
  class extends ApiCallCodeGen {
    static propTypes = {
      apiToken: PropTypes.string,
      apiUrl: PropTypes.string,
      header: PropTypes.func,
      showHeader: PropTypes.bool.isRequired,
    };

    static defaultProps = _.extend({}, ApiCallCodeGen.defaultProps, {
      codeItemMapper: BaseApiCallCodeGen.codeItemMapper,
    });

    render() {
      return (
        <BaseApiCallCodeGen
          {...this.props}
          denyList={EXPERIMENT_DENY_LIST}
          language={language}
          method="POST"
          name="experiment"
          path={["experiments"]}
          type="Experiment"
        />
      );
    }
  };

const CODE_ITEM_MAPPER = {
  arrayCode: ArrayCodeGen,
  jsonCode: JsonObjectCodeGen,
  keywordCode: KeywordCodeGen,
  primitiveCode: PrimitiveCodeGen,
};

const generateArrayInnerCode = function (
  codeItem,
  codeItemMapper,
  indent,
  language,
  jsonKey = null,
) {
  return (
    <CodeItemGenerator
      codeItem={codeItem}
      codeItemMapper={codeItemMapper}
      indent={indent}
      jsonKey={jsonKey}
      language={language}
    />
  );
};

export const generateJsonInnerCode = function (
  key,
  value,
  codeItemMapper,
  indent,
  language,
) {
  return generateArrayInnerCode(value, codeItemMapper, indent, language, key);
};

ArrayCodeGen.defaultProps = {
  codeItemMapper: CODE_ITEM_MAPPER,
  generateInnerCode: generateArrayInnerCode,
  indent: "",
  indentSize: INDENT,
};

JsonObjectCodeGen.defaultProps = {
  codeItemMapper: CODE_ITEM_MAPPER,
  denyList: JSON_OBJECT_DENY_LIST,
  generateInnerCode: generateJsonInnerCode,
  indent: "",
  indentSize: INDENT,
};

ApiCallCodeGen.defaultProps = _.extend({}, JsonObjectCodeGen.defaultProps, {
  apiToken: "SIGOPT_API_TOKEN",
  denyList: JSON_OBJECT_DENY_LIST,
  showHeader: true,
  showFooter: true,
});
