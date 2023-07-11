/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Favicon16x16Png from "../icons/favicon-16x16.png";
import Favicon32x32Png from "../icons/favicon-32x32.png";
import FaviconIco from "../icons/favicon.ico";
import {PAGE_TITLE, PRODUCT_NAME} from "../brand/constant";
import {headCodeString} from "./head_js";

export default class extends React.Component {
  static propTypes = {
    cssFiles: PropTypes.arrayOf(PropTypes.object).isRequired,
    forbidSearchEngineIndex: PropTypes.bool.isRequired,
    pageName: PropTypes.string,
    pageNamePrefix: PropTypes.string,
  };

  render() {
    const prefix = this.props.pageNamePrefix
      ? `${this.props.pageNamePrefix} - `
      : "";
    const subTitle = this.props.pageName && `${prefix}${this.props.pageName}`;
    const title = subTitle ? `${subTitle} - ${PRODUCT_NAME}` : PAGE_TITLE;

    const keywords = [
      "hyperparameter tuning",
      "Bayesian optimization",
      "machine learning",
      "model tuning",
      "grid search",
      "random search",
    ].join(", ");

    return (
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta
          name="description"
          content={
            `${PRODUCT_NAME} takes any research pipeline and tunes it, right in place, boosting your business objectives.` +
            " Our cloud-based ensemble of optimization algorithms is proven and seamless to deploy."
          }
        />
        <meta name="keywords" content={keywords} />
        <meta
          name="google-site-verification"
          content="D4PdqGWKVAygfwH93bQd8aAKNzEwHQPo815_FyZfppM"
        />
        {this.props.forbidSearchEngineIndex ? (
          <meta name="robots" content="noindex" />
        ) : null}

        <script
          id="init-code"
          dangerouslySetInnerHTML={{
            __html: headCodeString,
          }}
        />

        <title>{title}</title>

        {_.map(this.props.cssFiles, (cssFile) => (
          <link
            key={cssFile.href}
            type="text/css"
            rel={cssFile.rel || "stylesheet"}
            href={cssFile.href}
          />
        ))}

        <link rel="icon" type="image/x-icon" href={FaviconIco} />
        <link
          rel="icon"
          type="image/png"
          sizes="32x32"
          href={Favicon32x32Png}
        />
        <link
          rel="icon"
          type="image/png"
          sizes="16x16"
          href={Favicon16x16Png}
        />
      </head>
    );
  }
}
