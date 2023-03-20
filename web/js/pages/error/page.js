/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/error.less";

import React from "react";

import getErrorImage from "./images";
import {BLOG_URL, DOCS_URL, PRODUCTION_WEB_URL} from "../../net/constant";
import {PRODUCT_NAME} from "../../brand/constant";

class ErrorPage extends React.Component {
  header(code) {
    const defaultHeader = (
      <span>
        <h1>Uh oh - an unexpected error occurred.</h1>
        <p>Our team has been notified and are working to resolve the issue.</p>
        <p>
          In the meantime, you can try refreshing or going to one of the links
          below.
        </p>
      </span>
    );
    return (
      {
        400: (
          <span>
            <h1>There was something wrong with your request.</h1>
            {this.props.errorMsg && <p>{this.props.errorMsg}</p>}
          </span>
        ),
        404: (
          <span>
            <h1>We couldn&rsquo;t find the page you were looking for.</h1>
            {this.props.errorMsg && <p>{this.props.errorMsg}</p>}
            {this.props.loggedIn && (
              <p>These links below might help you get back on your way.</p>
            )}
            {!this.props.loggedIn && (
              <p>
                You may need to <a href="/login">log in</a> to view certain
                pages.
              </p>
            )}
          </span>
        ),
      }[code] || defaultHeader
    );
  }

  render() {
    const imageSrc = getErrorImage(this.props.status);
    return (
      <div className="error-page">
        <div className="container error-container">
          <div className="headline">
            {this.header(this.props.status)}
            {this.props.showTestError && (
              <div>
                <a
                  onClick={() =>
                    Promise.reject(
                      new Error("This is a test error, no cause for alarm"),
                    )
                  }
                >
                  Trigger test error
                </a>
              </div>
            )}
            <img className="squirrel" src={imageSrc} alt="Error Squirrel" />
          </div>
          <div className="row actions-row">
            <div className="col-md-3 col-xs-6">
              <p>Return to the {PRODUCT_NAME} landing page</p>
              <a href="/">Go back home</a>
            </div>
            <div className="col-md-3 col-xs-6">
              {this.props.loggedIn ? (
                <span>
                  <p>Your team&rsquo;s experiments and observations</p>
                  <a href="/experiments">See experiments</a>
                </span>
              ) : (
                <span>
                  <p>The world-class research powering {PRODUCT_NAME}</p>
                  <a href={`${PRODUCTION_WEB_URL}/research`}>
                    See the research
                  </a>
                </span>
              )}
            </div>
            <div className="col-md-3 col-xs-6">
              <p>Detailed documentation about our API endpoints</p>
              <a href={DOCS_URL}>Read the docs</a>
            </div>
            <div className="col-md-3 col-xs-6">
              <p>Articles and tutorials from the {PRODUCT_NAME} team</p>
              <a href={BLOG_URL}>Visit our blog</a>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default ErrorPage;
