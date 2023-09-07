/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/admin.less";

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import Component from "../../react/component";
import FieldEditor from "../../component/fieldeditor";
import PageTitle from "../../component/page_title";
import TabLink from "../../component/tab_link";
import schemas from "../../react/schemas";

export default class OrganizationDashboardPage extends Component {
  static propTypes = {
    alertBroker: schemas.AlertBroker.isRequired,
    canSeeExperimentsPage: PropTypes.bool,
    children: PropTypes.node,
    className: PropTypes.string,
    loginState: schemas.LoginState.isRequired,
    organization: PropTypes.object,
    path: PropTypes.string.isRequired,
    promiseApiClient: PropTypes.object.isRequired,
  };

  updateName = (id, val, s, e) => {
    this.props.promiseApiClient
      .organizations(this.props.loginState.organizationId)
      .update({name: val.name})
      .then(s, e);
  };

  render() {
    return (
      <div className={classNames("admin-page", this.props.className)}>
        <PageTitle
          title="Organization Admin"
          info={
            <FieldEditor
              alertBroker={this.props.alertBroker}
              fieldName="name"
              loginState={this.props.loginState}
              object={this.props.organization}
              buttonClassOverride="editable-info"
              updateFunction={this.updateName}
            />
          }
        >
          <nav>
            {this.props.canSeeExperimentsPage ? (
              <TabLink
                href={`/organization/${this.props.organization.id}/experiments`}
                path={this.props.path}
              >
                Experiments
              </TabLink>
            ) : null}
            <TabLink
              href={`/organization/${this.props.organization.id}/runs`}
              path={this.props.path}
            >
              Runs
            </TabLink>
            <TabLink
              href={`/organization/${this.props.organization.id}/users`}
              path={this.props.path}
            >
              Users
            </TabLink>
            <TabLink
              href={`/organization/${this.props.organization.id}/teams`}
              path={this.props.path}
            >
              Teams
            </TabLink>
          </nav>
        </PageTitle>
        {/* TODO: Make this a PageBody, will require some css tweaks */}
        <section className="page-body">
          <div className="container-fluid">
            <div className="row">
              <div className="admin-info">{this.props.children}</div>
            </div>
          </div>
        </section>
      </div>
    );
  }
}
