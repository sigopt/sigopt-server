/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/tokens.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Loading from "../../component/loading";
import Page from "../../component/page";
import ShareExperimentListModal from "../../share/share_modal_all";
import TokenRow from "../../token/row";
import TriggerModalButton from "../../component/modal/button";
import schemas from "../../react/schemas";
import {DOCS_URL} from "../../net/constant";
import {PagerMonitor} from "../../net/paging";
import {isDefinedAndNotNull} from "../../utils";

class TokenDashboardPage extends React.Component {
  static propTypes = {
    alertBroker: schemas.AlertBroker,
    canShare: PropTypes.bool.isRequired,
    client: schemas.Client,
    promiseApiClient: schemas.PromiseApiClient,
    sessionUpdater: schemas.SessionUpdater,
  };

  state = {
    experiments: null,
    tokens: [],
  };

  componentDidMount() {
    if (isDefinedAndNotNull(this.props.client)) {
      this.tokenMonitor = new PagerMonitor();
      this.props.promiseApiClient
        .clients(this.props.client.id)
        .tokens()
        .exhaustivelyPage({monitor: this.tokenMonitor})
        .then((result) => this.setState({tokens: result}));

      this.experimentMonitor = new PagerMonitor();
      this.props.promiseApiClient
        .clients(this.props.client.id)
        .experiments()
        .exhaustivelyPage({monitor: this.experimentMonitor})
        .then((result) => this.setState({experiments: result}));
    }
  }

  componentWillUnmount() {
    this.experimentMonitor.cancel();
    this.tokenMonitor.cancel();
  }

  generateTokenSuccess = (token) => {
    this.props.alertBroker.show(
      "Guest token successfully generated.",
      "success",
    );
    this.setState((prevState) => ({tokens: prevState.tokens.concat(token)}));
  };

  deleteTokenSuccess = (token) => {
    this.props.alertBroker.show("Guest token successfully deleted.", "info");
    this.setState((prevState) => ({
      tokens: _.reject(prevState.tokens, (t) => t.token === token.token),
    }));
  };

  render() {
    const tokens = _.sortBy(this.state.tokens, (t, index) =>
      t.all_experiments ? -1 : index,
    );
    const experimentMap = _.indexBy(this.state.experiments, "id");

    return (
      <Page
        className="token-dashboard-page"
        loggedIn={true}
        title="Token Dashboard"
      >
        <div className="header-row">
          <h2>API Tokens</h2>
          <p>
            <b>API Tokens</b> are what you will include in your production code.
            These tokens can view and modify every experiment on your team.
            These tokens do not have access to any of your personal sensitive
            account information.
          </p>
          <p>
            <b>Development Tokens</b> act in{" "}
            <a
              href={`${DOCS_URL}/core-module-api-references/api-topics/api-tokens-and-authentication#development-mode`}
            >
              development mode
            </a>{" "}
            and can be used for testing and development. Experiments created
            with this token will not receive intelligent suggestions, therefore
            it is unsuitable for use in production.
          </p>
          {this.props.canShare ? (
            <p>
              <b>Guest Tokens</b> are used to share experiment results with
              people who aren&rsquo;t on your team. When someone shares an
              experiment with a colleague, they can see the results for that
              experiment but they can&rsquo;t modify it or add any data. These
              tokens expire after 30 days.
            </p>
          ) : null}
          {this.props.canShare ? (
            <div className="generate-share-btn-holder">
              <TriggerModalButton
                className="paging-button btn btn-primary btn-sm generate-share-btn"
                label="Generate Guest Token"
              >
                <ShareExperimentListModal
                  {...this.props}
                  experiments={this.state.experiments}
                  onSubmitSuccess={(token) => this.generateTokenSuccess(token)}
                />
              </TriggerModalButton>
            </div>
          ) : null}
        </div>
        <Loading loading={_.isEmpty(tokens)} empty={_.isEmpty(tokens)}>
          <table className="table table-hover">
            <thead>
              <tr>
                <th>Type</th>
                <th>Token</th>
                <th>User ID</th>
                <th>Permissions</th>
                <th>Experiments</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {_.map(tokens, (token) => (
                <TokenRow
                  {...this.props}
                  deleteTokenSuccess={() => this.deleteTokenSuccess(token)}
                  experiment={experimentMap[token.experiment]}
                  key={token.token}
                  sessionUpdater={this.props.sessionUpdater}
                  token={token}
                />
              ))}
            </tbody>
          </table>
        </Loading>
      </Page>
    );
  }
}

export default TokenDashboardPage;
