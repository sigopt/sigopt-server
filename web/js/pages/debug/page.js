/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/debug.less";

import _ from "underscore";
import React from "react";

import CheckGlyph from "../../component/glyph/check";
import Page from "../../component/page";
import Spinner from "../../component/spinner";
import XmarkGlyph from "../../component/glyph/xmark";
import {PRODUCT_NAME} from "../../brand/constant";

const SectionItem = function (props) {
  return (
    <div className="section-row">
      <div className="section-description">{props.left}</div>
      <div className="section-status">{props.right}</div>
    </div>
  );
};

const Check = function (props) {
  let right;
  if (props.success) {
    right = <CheckGlyph />;
  } else if (props.loading) {
    right = <Spinner size={8} />;
  } else {
    right = <XmarkGlyph />;
  }
  return <SectionItem left={props.children} right={right} />;
};

class AjaxStatusCheck extends React.Component {
  state = {
    loading: true,
  };

  componentDidMount() {
    this.props.ajaxClient.request("GET", "/").then(
      () => this.setState({loading: false, success: true}),
      () => this.setState({loading: false, success: false}),
    );
  }

  render() {
    return (
      <Check loading={this.state.loading} success={this.state.success}>
        Network Status
      </Check>
    );
  }
}

class ApiStatusCheck extends React.Component {
  state = {
    loading: true,
  };

  componentDidMount() {
    // We don't care if the user is logged out, so treat auth failures as successes
    this.props.legacyApiClient.sessionDetail(
      () => this.setState({loading: false, success: true}),
      (error) => {
        const isUnauthed = error.status === 403 || error.status === 401;
        if (isUnauthed) {
          error.handle();
        }
        this.setState({loading: false, success: isUnauthed});
      },
    );
  }

  render() {
    return (
      <Check loading={this.state.loading} success={this.state.success}>
        API Status
      </Check>
    );
  }
}

class AuthStatusCheck extends React.Component {
  state = {
    loading: true,
  };

  componentDidMount() {
    this.props.legacyApiClient.userDetail(
      this.props.loginState.userId,
      (user) => this.setState({loading: false, userId: user.id}),
      () => this.setState({loading: false, userId: null}),
    );
  }

  render() {
    return (
      <Check
        loading={this.state.loading}
        success={this.state.userId === this.props.loginState.userId}
      >
        API Authorization
      </Check>
    );
  }
}

const Section = function (props) {
  return (
    <div className="section">
      <h2>{props.title}</h2>
      {props.children}
    </div>
  );
};

export default class extends React.Component {
  static displayName = "DebugPage";

  render() {
    return (
      <Page title="Troubleshooting" className="debug-page">
        <p className="description">
          Use this page to diagnose any issues you might be having connecting to{" "}
          {PRODUCT_NAME}.
        </p>
        <Section title="Assets">
          <Check success={true}>
            If you see a green checkmark, this page is working.
          </Check>
        </Section>
        <Section title="Network">
          <AjaxStatusCheck {...this.props} />
          <ApiStatusCheck {...this.props} />
          {this.props.loginState.userId && <AuthStatusCheck {...this.props} />}
        </Section>
        <Section title="Additional Information">
          <SectionItem
            left="Client ID"
            right={this.props.loginState.clientId || "None"}
          />
          <SectionItem
            left="User ID"
            right={this.props.loginState.userId || "None"}
          />
        </Section>
        <Section title="Headers">
          <ul>
            {_.chain(this.props.headers)
              .pairs()
              .sortBy((pair) => pair[0])
              .map(([key, value]) => (
                <li key={key}>
                  <span className="header-name">{key}</span>: {value}
                </li>
              ))
              .value()}
          </ul>
        </Section>
      </Page>
    );
  }
}
