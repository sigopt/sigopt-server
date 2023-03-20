/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Alert from "../alert/alert";
import Component from "../react/component";
import Navigation from "./navbar";
import Navlink from "./navlink";
import SessionPopper from "./session";
import schemas from "../react/schemas";
import {BLOG_URL, PRODUCTION_WEB_URL} from "../net/constant";
import {NewClientBanner} from "../component/new_client_banner";

export default class Chrome extends Component {
  static get propTypes() {
    return {
      alerts: PropTypes.arrayOf(PropTypes.object).isRequired,
      appUrl: PropTypes.string,
      canPopSession: PropTypes.bool.isRequired,
      content: PropTypes.oneOfType([
        PropTypes.element,
        PropTypes.shape({
          __html: PropTypes.string,
        }),
      ]).isRequired,
      csrfToken: PropTypes.string.isRequired,
      currentClient: schemas.Client,
      currentOrganization: schemas.Organization,
      currentUser: schemas.User,
      currentUserPermissions: PropTypes.arrayOf(schemas.Permission),
      currentUserMemberships: PropTypes.arrayOf(schemas.Membership),
      experiment: PropTypes.string,
      guestClientToken: schemas.Token,
      reactStrictMode: PropTypes.bool,
      showSidebarNav: PropTypes.bool.isRequired,
      loginState: schemas.LoginState.isRequired,
      path: PropTypes.string.isRequired,
      pageName: PropTypes.string,
      experimentCount: PropTypes.number,
      aiExperimentCount: PropTypes.number,
    };
  }

  componentDidMount() {
    _.map(this.props.alerts, (error) =>
      this.services.alertBroker.handle(new Alert(error)),
    );
  }

  render() {
    const contentHolder = _.has(this.props.content, "__html") ? (
      <div
        className="page-content"
        dangerouslySetInnerHTML={this.props.content}
      />
    ) : (
      <div className="page-content">{this.props.content}</div>
    );

    const footerLinks = (
      <>
        <Navlink
          {...this.props}
          navigator={this.services.navigator}
          href={`${PRODUCTION_WEB_URL}/research`}
        >
          Research
        </Navlink>
        <Navlink
          {...this.props}
          navigator={this.services.navigator}
          href={`${PRODUCTION_WEB_URL}/resources`}
        >
          Resources
        </Navlink>
        {!this.props.loginState.userId && (
          <Navlink
            {...this.props}
            navigator={this.services.navigator}
            href={`${PRODUCTION_WEB_URL}/contact`}
          >
            Contact
          </Navlink>
        )}
        <Navlink
          {...this.props}
          navigator={this.services.navigator}
          href={BLOG_URL}
        >
          Blog
        </Navlink>
      </>
    );

    const nav = (
      <Navigation
        ajaxClient={this.services.ajaxClient}
        alertBroker={this.services.alertBroker}
        appUrl={this.props.appUrl}
        currentClient={this.props.currentClient}
        currentOrganization={this.props.currentOrganization}
        currentUser={this.props.currentUser}
        currentUserPermissions={this.props.currentUserPermissions}
        currentUserMemberships={this.props.currentUserMemberships}
        footerLinks={this.props.showSidebarNav ? footerLinks : null}
        loginState={this.props.loginState}
        navigator={this.services.navigator}
        path={this.props.path}
        promiseApiClient={this.services.promiseApiClient}
        sessionUpdater={this.services.sessionUpdater}
        showSidebarNav={this.props.showSidebarNav}
        experimentCount={this.props.experimentCount}
        aiExperimentCount={this.props.aiExperimentCount}
      />
    );

    const isHome = this.props.path === "/home";

    const content = (
      <div>
        <div className="content" data-show-sidebar={this.props.showSidebarNav}>
          <div className="nav-background">{nav}</div>
          <div id="page-container">
            {this.props.canPopSession && (
              <SessionPopper
                csrfToken={this.props.csrfToken}
                currentClient={this.props.currentClient}
                currentUser={this.props.currentUser}
                experiment={this.props.experiment}
                guestClientToken={this.props.guestClientToken}
              />
            )}
            {isHome ? <NewClientBanner /> : null}
            <div id="flash-box" />
            {contentHolder}
            {!this.props.showSidebarNav && (
              <div className="footer">
                <nav
                  aria-label="Footer"
                  className="nav-section"
                  key="footer-links"
                  role="navigation"
                >
                  {footerLinks}
                </nav>
              </div>
            )}
          </div>
        </div>
      </div>
    );

    if (this.props.reactStrictMode) {
      return <React.StrictMode>{content}</React.StrictMode>;
    } else {
      return content;
    }
  }
}
