/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import YAML from "yaml";

import {ClickableTabs, Tab} from "../../component/tabs";
import {CodeBlock} from "../../component/code_block";

const TAB = "  ";

const indent = (line) => `${TAB}${line}`;

function listify(lines) {
  // lines should be a 2d array, where the first dimension represents each python object and the second dimension represents the lines of the python code for each object
  // adds commas to the end of the last line of each python object, except for the last object
  return _.flatten([
    ..._.chain(lines)
      .initial()
      .map((l) => [..._.initial(l), `${_.last(l)},`])
      .value(),
    _.last(lines),
  ]);
}

function pythonifyPrimitive(data) {
  const jsonRepr = JSON.stringify(data);
  return (
    {
      true: "True",
      false: "False",
      null: "None",
    }[jsonRepr] || jsonRepr
  );
}

function pythonify(data) {
  // convert the given data into lines of python code
  if (_.isArray(data)) {
    return _.flatten([
      "[",
      ..._.map(listify(_.map(data, pythonify)), indent),
      "]",
    ]);
  }
  if (_.isObject(data)) {
    return convertToPythonFunctionCall("dict", data);
  }
  return [pythonifyPrimitive(data)];
}

function convertToPythonFunctionKwargs(data) {
  const kwargs = _.map(data, (value, key) => {
    const lines = pythonify(value);
    return [`${key}=${_.first(lines)}`, ..._.rest(lines)];
  });
  return listify(kwargs);
}

function convertToPythonFunctionCall(functionName, kwargs) {
  return [
    `${functionName}(`,
    ..._.map(convertToPythonFunctionKwargs(kwargs), indent),
    ")",
  ];
}

export function yamlStringify(data) {
  return YAML.stringify(data, null, TAB);
}

export const CreateExperimentCodePython = ({content, includeImport}) => (
  <CodeBlock language="python">
    {(includeImport ? "import sigopt\n\n" : "") +
      convertToPythonFunctionCall("sigopt.create_experiment", content).join(
        "\n",
      )}
  </CodeBlock>
);

export const CreateExperimentCodeYaml = ({content, prepend}) => (
  <CodeBlock language="yaml">
    {(prepend || "") + yamlStringify(content)}
  </CodeBlock>
);

export class CreateExperimentCode extends React.Component {
  static propTypes = {
    content: PropTypes.string.isRequired,
  };

  render() {
    return (
      <ClickableTabs>
        <Tab label="Python">
          <CreateExperimentCodePython content={this.props.content} />
        </Tab>
        <Tab label="YAML">
          <CreateExperimentCodeYaml content={this.props.content} />
        </Tab>
      </ClickableTabs>
    );
  }
}

export class ExampleCodeSnippet extends React.Component {
  static propTypes = {
    pythonContent: PropTypes.string.isRequired,
    yamlContent: PropTypes.string.isRequired,
  };

  render() {
    return (
      <ClickableTabs>
        <Tab label="Python">
          <CodeBlock language="python">
            {pythonify(this.props.pythonContent).join("\n")}
          </CodeBlock>
        </Tab>
        <Tab label="YAML">
          <CodeBlock language="yaml">
            {yamlStringify(this.props.yamlContent)}
          </CodeBlock>
        </Tab>
      </ClickableTabs>
    );
  }
}
