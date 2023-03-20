/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import React from "react";

import AngleRightGlyph from "../../../component/glyph/angle-right";
import Component from "../../../react/component";
import {BLOG_URL, DOCS_URL} from "../../../net/constant";
import {PRODUCT_NAME} from "../../../brand/constant";

export default class LearnMore extends Component {
  render() {
    return (
      <>
        <h2>Learn More</h2>
        <div className="learn-more">
          <div className="get-started">
            <h3>Check Out Our Documentation</h3>
            <p>
              {PRODUCT_NAME}&apos;s documentation can help you get started
              quickly and show you the variety of features that we have to
              offer. Check it out to start optimizing now!
            </p>
            <a href={DOCS_URL}>
              Documentation&nbsp;
              <AngleRightGlyph />
            </a>
          </div>
          <div className="get-started">
            <h3>Optimization Topics</h3>
            <ul>
              <li>
                <a href={`${DOCS_URL}/intro/main-concepts`}>Main Concepts</a>
              </li>
              <li>
                <a
                  href={`${DOCS_URL}/advanced_experimentation/multimetric_optimization`}
                >
                  Multimetric Experiments
                </a>
              </li>
              <li>
                <a href={`${DOCS_URL}/advanced_experimentation/parallelism`}>
                  Parallel Optimization
                </a>
              </li>
              <li>
                <a
                  href={`${DOCS_URL}/advanced_experimentation/metric_thresholds`}
                >
                  Metric Thresholds
                </a>
              </li>
              <li>
                <a
                  href={`${DOCS_URL}/advanced_experimentation/metric_constraints`}
                >
                  Metric Constraints
                </a>
              </li>
            </ul>
          </div>
          <div className="get-started">
            <h3>Core Module Topics</h3>
            <ul>
              <li>
                <a href={`${DOCS_URL}/core-module-api-references/get_started`}>
                  Installation and Setup
                </a>
              </li>
              <li>
                <a href={`${DOCS_URL}/core-module-api-references/quick-start`}>
                  Quick Start Tutorial
                </a>
              </li>
              <li>
                <a
                  href={`${DOCS_URL}/core-module-api-references/api-topics/api-tokens-and-authentication`}
                >
                  API Tokens and Authentication
                </a>
              </li>
              <li>
                <a
                  href={`${DOCS_URL}/core-module-api-references/api-topics/manage-open-suggestions`}
                >
                  Manage Open Suggestions
                </a>
              </li>
              <li>
                <a
                  href={`${DOCS_URL}/core-module-api-references/api-topics/metadata`}
                >
                  Metadata
                </a>
              </li>
            </ul>
          </div>
          <div className="get-started">
            <h3>Record and Organize Model Runs</h3>
            <p>
              More and more modeling teams are looking for reliable tools to
              collaborate, track their work and reach the best models
              efficiently. In this post you&apos;ll learn how you can keep track
              of your machine learning progress, organize your model development
              efforts and use our Experiment Management capabilities.
            </p>
            <a
              href={`${BLOG_URL}/keeping-track-record-organize-model-training-runs/`}
            >
              Blog Post&nbsp;
              <AngleRightGlyph />
            </a>
          </div>
          <div className="get-started">
            <h3>AI Module Topics</h3>
            <ul>
              <li>
                <a href={`${DOCS_URL}/ai-module-api-references/get_started`}>
                  Installation and Setup
                </a>
              </li>
              <li>
                <a
                  href={`${BLOG_URL}/store-visual-artifacts-see-the-bigger-picture/`}
                >
                  Store Visual Artifacts
                </a>
              </li>
              <li>
                <a
                  href={`${BLOG_URL}/tips-for-tracking-analyzing-training-runs/`}
                >
                  Tips for Tracking and Analyzing Runs
                </a>
              </li>
              <li>
                <a href={`${DOCS_URL}/ai-module-api-references/byo_optimizer`}>
                  Bring Your Own Optimizer
                </a>
              </li>
              <li>
                <a href={`${DOCS_URL}/ai-module-api-references/api_reference`}>
                  API Reference
                </a>
              </li>
            </ul>
          </div>
        </div>
      </>
    );
  }
}
