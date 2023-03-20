/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";

import AnalysisPng from "./project_analysis.png";
import AngleRightGlyph from "../../../component/glyph/angle-right";
import Component from "../../../react/component";
import XmarkGlyph from "../../../component/glyph/xmark";
import modelCode from "../../docs/templates/short_model.ms";
import optimizeYaml from "../../docs/templates/short_optimize_yaml.ms";
import renderedtemplate from "../../docs/manuals/lib/renderedtemplate";
import runCmd from "./run_commands.ms";
import {ClickableTabs, Tab} from "../../../component/tabs";
import {CodeBlock} from "../../../component/code_block";
import {DOCS_URL, PUBLIC_ASSETS_URL} from "../../../net/constant";
import {PRODUCT_COMMAND_NAME} from "../../../brand/constant";

export const OptimizationExample = () => (
  <div className="code-example">
    <h3>Run a Short Example</h3>
    <p>Create two files in the same directory:</p>
    <ClickableTabs>
      {[
        <Tab label="model.py" key="model">
          <CodeBlock language="python">
            {renderedtemplate(modelCode, {
              moduleName: PRODUCT_COMMAND_NAME,
            })}
          </CodeBlock>
        </Tab>,
        <Tab label="experiment.yml" key="other">
          <CodeBlock language="yaml">
            {renderedtemplate(optimizeYaml)}
          </CodeBlock>
        </Tab>,
      ]}
    </ClickableTabs>
    <p>Then run the following commands in the Terminal:</p>
    <CodeBlock language="bash">
      {renderedtemplate(runCmd, {
        cmd: "sigopt optimize -e experiment.yml python model.py",
        moduleName: PRODUCT_COMMAND_NAME,
      })}
    </CodeBlock>
  </div>
);

const RunsExample = () => (
  <div className="code-example">
    <h3>Run a Short Example</h3>
    <ClickableTabs>
      {[
        <Tab label="model.py" key="model">
          <CodeBlock language="python">
            {renderedtemplate(modelCode, {
              moduleName: PRODUCT_COMMAND_NAME,
            })}
          </CodeBlock>
        </Tab>,
      ]}
    </ClickableTabs>
    <p>Then run the following commands in the terminal:</p>
    <CodeBlock language="bash">
      {renderedtemplate(runCmd, {
        cmd: "sigopt run python model.py",
        moduleName: PRODUCT_COMMAND_NAME,
      })}
    </CodeBlock>
  </div>
);

const welcomeContent = {
  optimize: {
    tutorialLink:
      "https://colab.research.google.com/github/sigopt/sigopt-examples/blob/b73b2332a1975291267c417cd2c070555ea66d86/get-started/sigopt_experiment_and_optimization_demo.ipynb",
    docsLink: `${DOCS_URL}/ai-module-api-references/tutorial/experiment`,
    videoLink: `${PUBLIC_ASSETS_URL}/get-started-notebooks/v2/getting_started_with_optimization.mp4`,
    videoTitle: "Watch an Optimization Example",
    example: <OptimizationExample />,
  },
  track: {
    tutorialLink:
      "https://colab.research.google.com/github/sigopt/sigopt-examples/blob/b73b2332a1975291267c417cd2c070555ea66d86/get-started/sigopt_runs_demo.ipynb",
    docsLink: `${DOCS_URL}/ai-module-api-references/tutorial/run`,
    videoLink: `${PUBLIC_ASSETS_URL}/get-started-notebooks/v2/getting_started_with_runs.mp4`,
    videoTitle: "Watch a Run Example",
    example: <RunsExample />,
  },
};

export default class Welcome extends Component {
  static propTypes = {
    hide: PropTypes.func.isRequired,
    showRunsContent: PropTypes.bool,
  };

  render() {
    const content = this.props.showRunsContent
      ? welcomeContent.track
      : welcomeContent.optimize;
    return (
      <div className="welcome">
        <h1>Welcome to SigOpt!</h1>
        <div className="close" onClick={this.props.hide}>
          <XmarkGlyph />
        </div>
        <div className="col-1">
          <div className="description">
            <p>
              You can easily track runs, visualize training, and scale
              hyperparameter optimization for any model, library, and
              infrastructure.
            </p>
            <p>
              Learn how to make the most of SigOpt features by watching the
              video tutorial, or reviewing example code.
            </p>
            <ul>
              <li>
                <a href={content.tutorialLink}>
                  Google Colab Tutorial&nbsp;
                  <AngleRightGlyph />
                </a>
              </li>
              <li>
                <a href={content.docsLink}>
                  See Docs Tutorial&nbsp;
                  <AngleRightGlyph />
                </a>
              </li>
            </ul>
          </div>
          <h3>{content.videoTitle}</h3>
          <video controls={true} src={content.videoLink}>
            <img src={AnalysisPng} />
          </video>
        </div>
        <div className="col-2">{content.example}</div>
      </div>
    );
  }
}
