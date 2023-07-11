/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Url from "../net/url";
import {MODAL_ROOT_ID} from "../component/modal/constant";

export default class extends React.Component {
  static propTypes = {
    children: PropTypes.node.isRequired,
    csrfToken: PropTypes.string.isRequired,
    includeJs: PropTypes.bool.isRequired,
    jsFiles: PropTypes.arrayOf(
      PropTypes.shape({
        async: PropTypes.bool,
        defer: PropTypes.bool,
        params: PropTypes.object,
        src: PropTypes.string.isRequired,
      }),
    ).isRequired,
  };

  render() {
    return (
      <body>
        <noscript>
          <div className="alert alert-danger" style={{marginTop: 50}}>
            This site requires the use of Javascript. Please enable Javascript
            to proceed.
          </div>
        </noscript>

        {this.props.children}

        <div className="csrf-token" style={{display: "none"}}>
          {this.props.csrfToken}
        </div>

        {/* These are scripts needed on just about every page */}
        {this.props.includeJs ? (
          <div>
            {_.map(this.props.jsFiles, (jsFile) => {
              const url = new Url(jsFile.src);
              url.params = jsFile.params || {};
              return (
                <script
                  async={jsFile.async || false}
                  crossOrigin={jsFile.crossOrigin}
                  defer={jsFile.defer || false}
                  key={jsFile.src}
                  src={url}
                  type="text/javascript"
                />
              );
            })}
          </div>
        ) : null}

        <div id={MODAL_ROOT_ID} />
      </body>
    );
  }
}
