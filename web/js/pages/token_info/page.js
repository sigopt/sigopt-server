/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/token_info.less";

import _ from "underscore";
import React from "react";

import Page from "../../component/page";
import ReadOnlyInput from "../../component/readonly";
import {DOCS_URL} from "../../net/constant";

class BlockContent extends React.Component {
  render() {
    if (this.props.label) {
      return (
        <div className={this.props.className}>
          <label key="label" className="control-label">
            {this.props.label}
          </label>
          <div key="content" className="control-content">
            {this.props.children}
          </div>
        </div>
      );
    } else {
      return (
        <div className={this.props.className}>
          <div className="control-content offset">{this.props.children}</div>
        </div>
      );
    }
  }
}

const DataBlock = function (props) {
  return (
    <div className="data-block">
      <h2>{props.heading}</h2>
      <div className="form-horizontal">
        {React.Children.map(
          props.children,
          (child) => child && <div className="form-group">{child}</div>,
        )}
      </div>
    </div>
  );
};

export default class TokenInfoPage extends React.Component {
  render() {
    const canSwitchTeams = _.size(this.props.currentUserPermissions) > 1;
    return (
      <Page loggedIn={true} title="API Tokens" className="token-info-page">
        <DataBlock>
          {this.props.client && canSwitchTeams ? (
            <BlockContent label="Team">
              <ReadOnlyInput name="team-name" value={this.props.client.name} />
            </BlockContent>
          ) : null}
          {this.props.client ? (
            <BlockContent label="Client ID">
              <ReadOnlyInput name="client-id" value={this.props.client.id} />
            </BlockContent>
          ) : null}
          {this.props.user ? (
            <BlockContent label="User ID">
              <ReadOnlyInput value={this.props.user.id} />
            </BlockContent>
          ) : null}
          {this.props.clientToken ? (
            <BlockContent label="API Token">
              <ReadOnlyInput
                name="api-token"
                value={this.props.clientToken.token}
              />
            </BlockContent>
          ) : null}
          {this.props.developmentToken ? (
            <BlockContent label="Development Token">
              <ReadOnlyInput
                name="dev-token"
                value={this.props.developmentToken}
              />
            </BlockContent>
          ) : null}
          <div className="api-token-links">
            <div className="btn-holder">
              <a className="btn btn-white-border" href="/tokens/manage">
                Manage Tokens
              </a>
            </div>
            <div className="btn-holder">
              <a
                href={`${DOCS_URL}/core-module-api-references/api-topics/api-tokens-and-authentication`}
              >
                Learn more about tokens
              </a>
            </div>
          </div>
        </DataBlock>
      </Page>
    );
  }
}
