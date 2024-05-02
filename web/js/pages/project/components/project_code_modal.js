/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";

import Component from "../../../react/component";
import ModalForm from "../../../component/modal/form";
import frankeTemplatePython from "../../docs/templates/franke_python_p1.ms";
import frankeTemplateR from "../../docs/templates/franke_r_p1.ms";
import renderedTemplate from "../../docs/manuals/lib/renderedtemplate";
import {CodeBlock} from "../../../component/code_block";
import {DOCS_URL} from "../../../net/constant";
import {Dropdown, DropdownItem} from "../../../component/dropdown";
import {FooterTypes} from "../../../component/modal/constant";

export default class ProjectCodeModal extends Component {
  constructor(...args) {
    super(...args);
    this.state = {
      language: "Python",
    };
    this._projectModal = React.createRef();
  }

  show = () => this._projectModal.current && this._projectModal.current.show();

  render() {
    const languageToPages = {
      Python: (
        <CodeBlock language="python">
          {renderedTemplate(frankeTemplatePython, this.props)}
        </CodeBlock>
      ),
      R: (
        <CodeBlock language="r">
          {renderedTemplate(frankeTemplateR, this.props)}
        </CodeBlock>
      ),
    };

    return (
      <ModalForm
        cancelButtonLabel="Close"
        footer={FooterTypes.Cancel}
        title={`Create an experiment in ${this.props.project.name}`}
        ref={this._projectModal}
      >
        <div className="project-code-modal">
          <p>
            Add to a project directly by setting the <code>project</code> field
            during experiment creation.{""}
            <br />
            <a
              href={`${DOCS_URL}/ai-module-api-references/tutorial/project-tutorial`}
              target="_blank"
              rel="noopener noreferrer"
            >
              {" "}
              Learn more about Projects.
            </a>
          </p>
          <div className="language-selector">
            <p>Select a language:</p>
            <Dropdown
              buttonClassName="btn btn-default"
              label={this.state.language}
            >
              {_.map(Object.keys(languageToPages), (lang) => (
                <DropdownItem className={lang} key={lang}>
                  <a onClick={() => this.setState({language: lang})}>{lang}</a>
                </DropdownItem>
              ))}
            </Dropdown>
          </div>
          <div className="code-example">
            {languageToPages[this.state.language]}
          </div>
        </div>
      </ModalForm>
    );
  }
}
