/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../styles/less/user.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import FieldEditor from "../../component/fieldeditor";
import Page from "../../component/page";
import ResendVerificationEmailButton from "../../user/resend";
import schemas from "../../react/schemas";
import {clientPermissionsDisplayText} from "../../user/helpers";

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

class UserOrganizations extends React.Component {
  static propTypes = {
    memberships: PropTypes.arrayOf(schemas.Membership.isRequired).isRequired,
    permissionsMap: PropTypes.objectOf(
      PropTypes.arrayOf(schemas.Permission.isRequired).isRequired,
    ).isRequired,
  };

  render() {
    const numOrganizations = _.size(this.props.memberships);
    const numTeams = _.reduce(
      _.values(this.props.permissionsMap),
      (memo, permissions) => memo + _.size(permissions),
      0,
    );
    return (
      <DataBlock heading="My Organizations">
        <div className="organizations-list-section">
          {numTeams > 1 && (
            <p>
              You are on {numTeams} teams{" "}
              {numOrganizations > 1
                ? `across ${numOrganizations} organizations.`
                : "in 1 organization."}
            </p>
          )}
          {_.chain(this.props.memberships)
            .map((m) => (
              <div
                className="organization-info-section"
                data-id={m.organization.id}
                key={m.organization.id}
              >
                <h3>
                  {m.organization.name} {m.type === "owner" ? "(Owner)" : ""}
                </h3>
                <table className="table teams-table">
                  <thead>
                    <tr key="header">
                      <th>Team</th>
                      <th>Role</th>
                    </tr>
                  </thead>
                  <tbody>
                    {_.map(
                      this.props.permissionsMap[m.organization.id],
                      (permission) => {
                        const clientId = permission.client.id;
                        return (
                          <tr
                            data-id={clientId}
                            key={clientId}
                            className="team-info-row"
                          >
                            <td>{permission.client.name}</td>
                            <td>{clientPermissionsDisplayText(permission)}</td>
                          </tr>
                        );
                      },
                    )}
                  </tbody>
                </table>
              </div>
            ))
            .value()}
        </div>
      </DataBlock>
    );
  }
}

const InvitedBlock = function (props) {
  if (!_.isEmpty(props.userPermissionsMap)) {
    return (
      <UserOrganizations
        memberships={props.userMemberships}
        permissionsMap={props.userPermissionsMap}
      />
    );
  } else if (!_.isEmpty(props.userPendingPermissions)) {
    return (
      <DataBlock heading="Team Info">
        <p className="no-client-description">
          You must verify your email before you can accept your invite to join
          the {_.first(props.userPendingPermissions).client_name} team. Or, you
          can <a href="/clients/create">create your own team</a>.
        </p>
      </DataBlock>
    );
  }
  return null;
};

export default class extends React.Component {
  static displayName = "UserProfilePage";

  componentDidMount() {
    if (this.props.error) {
      this.props.alertBroker.show(this.props.error);
    }
  }

  render() {
    return (
      <Page loggedIn={true} title="My Profile" className="user-profile-page">
        <DataBlock heading="User Info">
          <BlockContent label="Name" className="field">
            <FieldEditor
              alertBroker={this.props.alertBroker}
              fieldName="name"
              loginState={this.props.loginState}
              object={this.props.user}
              updateFunction={this.props.legacyApiClient.userUpdate}
            />
          </BlockContent>
          <BlockContent label="Email">
            <p>{this.props.user.email}</p>
          </BlockContent>
          {this.props.shouldVerifyEmail && (
            <BlockContent label=" ">
              <ResendVerificationEmailButton {...this.props} size="xs" />
            </BlockContent>
          )}
          <BlockContent label="Password">
            <a href="/change_password">Change</a>
          </BlockContent>
          <BlockContent label="Account">
            <a href="/user/i_want_to_delete_my_account">Delete Account</a>
          </BlockContent>
        </DataBlock>
        <InvitedBlock {...this.props} />
      </Page>
    );
  }
}
