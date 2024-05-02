/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/experiment/api.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ExperimentPage from "../../page_wrapper";
import HistoryTracker from "../../../../net/history";
import schemas from "../../../../react/schemas";
import ui from "../../../../experiment/ui";
import {CopyableText} from "../../../../component/code_block";
import {
  CreateExperimentCodePython,
  CreateExperimentCodeYaml,
} from "../../../docs/codegen";
import {EXPERIMENT_DENY_LIST} from "../../../../component/code_generator/base";
import {PythonExperimentCodeGen} from "../../../../component/code_generator/python";
import {RExperimentCodeGen} from "../../../../component/code_generator/r";
import {recursivelyCondenseObject} from "../../../../utils";

const sanitizeExperimentForCreate = (experiment) =>
  _.omit(experiment, EXPERIMENT_DENY_LIST.concat(["project"]));

const PythonRunApiCodeGen = ({codeItem}) => (
  <CreateExperimentCodePython
    content={sanitizeExperimentForCreate(codeItem)}
    includeImport={true}
  />
);
const YamlRunApiCodeGen = ({codeItem}) => (
  <CreateExperimentCodeYaml
    content={sanitizeExperimentForCreate(codeItem)}
    prepend={"# experiment.yml\n\n"}
  />
);

const CORE_MODULE_CODE_MAP = {
  python: (props) => (
    <CopyableText>
      <PythonExperimentCodeGen {...props} />
    </CopyableText>
  ),
  r: (props) => (
    <CopyableText>
      <RExperimentCodeGen {...props} />
    </CopyableText>
  ),
};

const AI_MODULE_CODE_MAP = {
  python: PythonRunApiCodeGen,
  yaml: YamlRunApiCodeGen,
};

const languageTitles = {
  python: "Python",
  r: "R",
  yaml: "YAML",
};

export default class ExperimentApiPage extends React.Component {
  static propTypes = {
    apiToken: PropTypes.string,
    apiUrl: PropTypes.string,
    experiment: schemas.Experiment.isRequired,
    loginState: schemas.LoginState.isRequired,
    pageParams: PropTypes.shape({
      language: PropTypes.string,
    }),
  };

  constructor(...args) {
    super(...args);
    this.codeMap = ui.isAiExperiment(this.props.experiment)
      ? AI_MODULE_CODE_MAP
      : CORE_MODULE_CODE_MAP;
    this.state = {};
    this.historyTracker = new HistoryTracker();
  }

  componentDidMount() {
    this.handleLanguageSelect((this.props.pageParams || {}).language);
  }

  componentDidUpdate(prevProps, prevState) {
    if (prevState.language !== this.state.language) {
      this.historyTracker.setBrowserUrl(`?language=${this.state.language}`);
    }
  }

  generateCode(language, experiment) {
    const CodeGen = this.codeMap[language];
    if (!CodeGen) {
      return null;
    }
    const apiToken = this.props.apiToken || "SIGOPT_API_TOKEN";
    const apiUrl = this.props.apiUrl;

    const props = {
      apiToken: apiToken,
      apiUrl: apiUrl,
      codeItem: experiment,
      language: language,
    };
    return <CodeGen {...props} />;
  }

  handleLanguageSelect(language) {
    this.setState((state) => {
      const lowerLanguage = (language || "").toLowerCase();
      if (_.contains(_.keys(this.codeMap), lowerLanguage)) {
        return {language: lowerLanguage};
      }
      if (!state.language) {
        return {language: _.first(_.keys(this.codeMap))};
      }
      return {};
    });
  }

  render() {
    return (
      <ExperimentPage
        {...this.props}
        experiment={this.props.experiment}
        loginState={this.props.loginState}
        className="experiment-api-page"
      >
        <div className="selection-form">
          <div className="language-selection-container">
            <div className="selection-dropdown">
              <select
                name="language"
                onChange={(e) => this.handleLanguageSelect(e.target.value)}
                value={this.state.language}
              >
                {_.map(_.keys(this.codeMap), (item, key) => (
                  <option key={key} value={item}>
                    {languageTitles[item]}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
        {this.generateCode(
          this.state.language,
          recursivelyCondenseObject(this.props.experiment),
        )}
      </ExperimentPage>
    );
  }
}
