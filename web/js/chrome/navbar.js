/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../render/bootstrap";
import "./navbar.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ArrowUpRightFromSquareGlyph from "../component/glyph/arrow-up-right-from-square";
import BarsGlyph from "../component/glyph/bars";
import ChevronDownGlyph from "../component/glyph/chevron-down";
import ChevronUpGlyph from "../component/glyph/chevron-up";
import Navlink from "./navlink";
import SigOptLogoHorizSvg from "./SigOpt_logo_horiz.svg";
import refreshPage from "../net/refresh";
import schemas from "../react/schemas";
import {DOCS_URL, PRODUCTION_WEB_URL} from "../net/constant";
import {LogoutLink} from "./logout";
import {SIGNUP_CLICK} from "./constants";
import {isDefinedAndNotNull} from "../utils";

class SelectionList extends React.Component {
  static propTypes = {
    currentEntity: PropTypes.object.isRequired,
    entities: PropTypes.arrayOf(PropTypes.object).isRequired,
    label: PropTypes.string,
    org: PropTypes.bool.isRequired,
    permissionsMap: PropTypes.object,
    selectClient: PropTypes.func.isRequired,
  };

  getClientId(id) {
    if (this.props.org) {
      return _.first(this.props.permissionsMap[id]).client.id;
    } else {
      return id;
    }
  }

  render() {
    return (
      <div className="nav-section" data-type={this.props.org ? "org" : "team"}>
        {this.props.label && <label>{this.props.label}</label>}
        <p className="nav-link active">{this.props.currentEntity.name}</p>
        {this.props.entities.length > 0 ? (
          <div>
            {_.chain(this.props.entities)
              .sortBy((o) => o.name.toLowerCase())
              .map((o) => (
                <a
                  key={o.name}
                  data-id={this.getClientId(o.id)}
                  className="nav-link"
                  onClick={() =>
                    this.props.selectClient(this.getClientId(o.id))
                  }
                >
                  {o.name}
                </a>
              ))
              .value()}
          </div>
        ) : null}
      </div>
    );
  }
}

class NavbarContent extends React.Component {
  static propTypes = {
    aiExperimentCount: PropTypes.number,
    ajaxClient: schemas.AjaxClient.isRequired,
    alertBroker: schemas.AlertBroker.isRequired,
    currentClient: schemas.Client,
    currentOrganization: schemas.Organization,
    currentUser: schemas.User,
    currentUserMemberships: PropTypes.arrayOf(schemas.Membership),
    currentUserPermissions: PropTypes.arrayOf(schemas.Permission),
    experimentCount: PropTypes.number,
    footerLinks: PropTypes.node,
    loginState: schemas.LoginState.isRequired,
    navigator: schemas.Navigator.isRequired,
    path: PropTypes.string.isRequired,
    promiseApiClient: schemas.PromiseApiClient.isRequired,
    sessionUpdater: schemas.SessionUpdater.isRequired,
    showSidebarNav: PropTypes.bool.isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = {
      organizationPermissionMap: _.chain(this.props.currentUserPermissions)
        .groupBy((p) => p.client.organization)
        .mapObject((permissions) =>
          _.sortBy(permissions, (p) => p.client.name.toLowerCase()),
        )
        .value(),
      expandedUserAccordion: false,
    };
  }

  toggleAccordion = (e) => {
    e.preventDefault();
    this.setState((prevState) => ({
      expandedUserAccordion: !prevState.expandedUserAccordion,
    }));
  };

  selectClient = (clientId) => {
    this.props.alertBroker.clearAlerts();
    this.props.sessionUpdater
      .setApiToken(this.props.loginState.apiToken, clientId)
      .then(
        () =>
          // We want the user to stay on this page if they still have permission,
          // otherwise redirect to a safe home page
          this.props.ajaxClient
            .get(window.location)
            .then(refreshPage, () => this.props.navigator.navigateTo("/")),
        this.props.alertBroker.errorHandlerThatExpectsStatus(400),
      );
  };

  render() {
    const hasClient =
      this.props.currentClient && this.props.currentOrganization;
    const organizationId =
      this.props.currentOrganization && this.props.currentOrganization.id;
    const showOrganizationDashboard =
      hasClient &&
      _.any(
        this.state.organizationPermissionMap[organizationId],
        (permission) => permission.is_owner || permission.can_admin,
      );
    const currentMembership =
      this.props.currentOrganization &&
      _.find(
        this.props.currentUserMemberships,
        (m) => m.organization.id === organizationId,
      );
    const ownsCurrentOrganization =
      currentMembership && currentMembership.type === "owner";
    const orgAdminLink =
      showOrganizationDashboard &&
      organizationId &&
      (ownsCurrentOrganization
        ? `/organization/${organizationId}/experiments`
        : `/organization/${organizationId}/users`);
    const clients = _.chain(this.props.currentUserPermissions)
      .map((o) => o.client)
      .filter((c) => c.organization === organizationId)
      .filter((c) => c.name !== this.props.currentClient.name)
      .value();
    const orgs = _.chain(this.props.currentUserMemberships)
      .map((m) => m.organization)
      .filter((o) => o.id !== organizationId)
      .value();

    const loggedOutLinks = [
      <Navlink
        {...this.props}
        href={`${PRODUCTION_WEB_URL}/solution`}
        key="solution"
      >
        Solution
      </Navlink>,
      <Navlink
        {...this.props}
        href={`${PRODUCTION_WEB_URL}/product`}
        key="product"
      >
        Product
      </Navlink>,
      <div key="divider2" className="vertical-divider" />,
      <Navlink {...this.props} href="/login" key="login">
        Log In
      </Navlink>,
      <Navlink
        {...this.props}
        className="cta"
        href="/signup"
        onClick={(e) =>
          document.dispatchEvent(
            // If this event is not handled (by calling e.detail.clickEvent.preventDefault())
            // then we fallback to the default behaviour of going to the pricing page. This
            // allows pages to override this behaviour
            new CustomEvent(SIGNUP_CLICK, {detail: {clickEvent: e}}),
          )
        }
        key="try-it"
      >
        Sign Up
      </Navlink>,
    ];

    // Made for use in Docs pages, could be used in other non-app sections where an
    // authenticated user may want to navigate to the app landing page
    const topBarLinks = [
      <Navlink {...this.props} href="/home" key="home">
        Home
      </Navlink>,
    ];

    const appLinks = [
      this.props.currentUser && (
        <React.Fragment key="user">
          <div className="nav-section">
            <label>ACCOUNT DETAILS</label>
          </div>
          <div
            className="nav-section"
            data-open-accordion={this.state.expandedUserAccordion}
          >
            <div id="accordion-header" onClick={this.toggleAccordion}>
              <div className="nav-link">
                {this.props.currentUser.name}
                <React.Fragment key="user-accordion">
                  {this.state.expandedUserAccordion ? (
                    <ChevronUpGlyph />
                  ) : (
                    <ChevronDownGlyph />
                  )}
                </React.Fragment>
              </div>
            </div>
            <div
              id="accordion-links"
              data-open-accordion={this.state.expandedUserAccordion}
            >
              <div className="nav-section">
                <Navlink {...this.props} className="nav-link" href="/user/info">
                  My Profile
                </Navlink>
                {this.props.loginState.clientId && (
                  <Navlink {...this.props} href="/tokens/info" key="profile">
                    API Tokens
                  </Navlink>
                )}
              </div>
              {this.props.currentOrganization && (
                <>
                  <hr />
                  <SelectionList
                    currentEntity={this.props.currentOrganization}
                    entities={orgs}
                    label="Organization"
                    org={true}
                    permissionsMap={this.state.organizationPermissionMap}
                    selectClient={this.selectClient}
                  />
                </>
              )}
              {this.props.currentClient && (
                <>
                  <hr />
                  <SelectionList
                    currentEntity={this.props.currentClient}
                    entities={clients}
                    label="Team"
                    org={false}
                    permissionsMap={this.state.organizationPermissionMap}
                    selectClient={this.selectClient}
                  />
                </>
              )}
              <hr />
              <div className="nav-section">
                <LogoutLink
                  className="nav-link"
                  continue={this.props.path}
                  csrfToken={this.props.loginState.csrfToken}
                >
                  Log Out
                </LogoutLink>
              </div>
            </div>
            <hr />
          </div>
        </React.Fragment>
      ),
      orgAdminLink && (
        <React.Fragment key="admin">
          <div className="nav-section">
            <label>ADMIN</label>
            <Navlink {...this.props} href={orgAdminLink}>
              Organization Admin
            </Navlink>
          </div>
          <hr />
        </React.Fragment>
      ),
      this.props.loginState.clientId && (
        <div className="nav-section" key="content">
          <div className="nav-subsection">
            <label>MY SIGOPT</label>
            <Navlink {...this.props} href="/home" key="home">
              Home
            </Navlink>
          </div>
          <div className="nav-subsection">
            <label>CORE MODULE</label>
            <Navlink
              {...this.props}
              href="/experiments"
              key="experiments"
              isEmpty={this.props.experimentCount === 0}
            >
              Experiments
            </Navlink>
          </div>
          <div className="nav-subsection">
            <label>AI MODULE</label>
            <Navlink
              {...this.props}
              href="/projects"
              key="projects"
              isEmpty={this.props.aiExperimentCount === 0}
            >
              Projects
            </Navlink>
            <Navlink
              {...this.props}
              href="/aiexperiments"
              key="aiexperiments"
              isEmpty={this.props.aiExperimentCount === 0}
            >
              Experiments
            </Navlink>
          </div>
        </div>
      ),
    ];

    const loggedInLinks = this.props.showSidebarNav ? appLinks : topBarLinks;

    return (
      <>
        <nav
          aria-label="Main"
          className="main-menu"
          key="main-links"
          role="navigation"
        >
          {this.props.loginState.userId ? loggedInLinks : loggedOutLinks}
        </nav>
        {this.props.footerLinks && (
          <>
            <hr />
            <nav
              aria-label="Footer"
              className="nav-section"
              key="footer-links"
              role="navigation"
            >
              <label>
                External Links <ArrowUpRightFromSquareGlyph />
              </label>
              <a
                className="nav-link"
                href={DOCS_URL}
                target="_blank"
                rel="noopener noreferrer"
                key="docs"
              >
                Docs
              </a>
              {this.props.footerLinks}
              <a
                className="nav-link"
                href={`${DOCS_URL}/support`}
                target="_blank"
                rel="noopener noreferrer"
                key="support"
              >
                Support
              </a>
            </nav>
          </>
        )}
      </>
    );
  }
}

export default (props) => (
  <div className="navbar">
    <div className="brand-menu-bar">
      <a
        className="brand"
        href={
          isDefinedAndNotNull(props.loginState.clientId)
            ? "/"
            : PRODUCTION_WEB_URL
        }
        key="brand"
      >
        <img src={SigOptLogoHorizSvg} />
      </a>
      <button
        aria-controls="collapsible-navbar"
        aria-expanded="false"
        className="navbar-toggle collapsed"
        data-target="#collapsible-nav"
        data-toggle="collapse"
        key="nav-toggle"
        type="button"
      >
        <span className="sr-only">Toggle navigation</span>
        <BarsGlyph key="menu-bars" />
      </button>
    </div>
    <div
      id="collapsible-nav"
      role="navigation"
      className="navbar-collapse collapse"
    >
      <div className="nav-menu-layout">
        <NavbarContent {...props} />
      </div>
    </div>
  </div>
);
