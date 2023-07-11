/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/organization/users.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import React from "react";
import {Typeahead} from "react-bootstrap-typeahead";

import ActionButton from "../../../component/action_button";
import ClientsDropdown from "../../../client/dropdown";
import NetError from "../../../alert/error";
import OrganizationDashboardPage from "../page_wrapper";
import ReadOnlyInput from "../../../component/readonly";
import RotateTokenModal from "../../../token/rotate_token_modal";
import TriggerModalButton from "../../../component/modal/button";
import Url from "../../../net/url";
import refreshPage from "../../../net/refresh";
import {CreateInviteAdminModal} from "./modal/create_invite_admin";
import {CreateInviteOwnerModal} from "./modal/create_invite_owner";
import {EditTeamsModal} from "./modal/edit_teams";
import {InviteRoles} from "../../../user/roles";
import {MembershipTable, TableType} from "./membership_table/table";
import {PRODUCT_NAME} from "../../../brand/constant";
import {RotateButton} from "../../../component/buttons";
import {extractDomainFromEmail} from "../../../net/email";

const InputGroup = (props) => (
  <div className="panel panel-default">
    <div className="panel-heading">{props.title}</div>
    <div className="panel-body">{props.children}</div>
  </div>
);

const Control = (props) => (
  <div className="permission-control">
    {props.label ? <label>{props.label}</label> : null}
    {props.children}
  </div>
);

const RadioControl = (props) => {
  const id = Math.random().toString();
  return (
    <Control>
      {props.children}
      <div className="radio">
        <label htmlFor={id}>
          <input
            name={props.name}
            type="radio"
            id={id}
            checked={props.checked}
            onChange={props.onChange}
          />
          {""}
          {props.label}
        </label>
      </div>
    </Control>
  );
};

const ReadOnlyControl = (props) => (
  <Control label={props.label}>
    <div className="signup-link-holder">
      <div className="signup-link">
        <ReadOnlyInput value={props.value} />
      </div>
      {props.children}
    </div>
  </Control>
);

const RotateInputButton = (props) => (
  <div className="rotate-button-holder">
    <div className="rotate-button-holder">
      <TriggerModalButton
        button={<RotateButton />}
        disabled={props.disabled}
        title="Rotate Token"
      >
        <RotateTokenModal
          promiseApiClient={props.promiseApiClient}
          loginState={props.loginState}
          success={props.onRotate}
          token={props.signupToken}
        >
          <p>
            Are you sure you want to rotate this link? This will permanently
            invalidate the link, and replace it with a new one.
          </p>
        </RotateTokenModal>
      </TriggerModalButton>
    </div>
  </div>
);

const DefaultTeamControl = (props) => (
  <Control label="Initial Team">
    <p>
      When users sign up, select the team that they will join by default. They
      will be granted Write permissions within that team.
    </p>
    <ClientsDropdown
      allowBlank={false}
      clients={props.clients}
      onClientSelect={props.onClientSelect}
      selectedClient={_.find(props.clients, (c) => c.id === props.signupClient)}
    />
  </Control>
);

class SignupPermissionsEditor extends React.Component {
  state = {
    allowSignupLink:
      this.props.organization.allow_signup_from_email_domains || false,
    domains: this.props.organization.email_domains || [],
    error: null,
    needsSave: false,
    rotated: false,
    signupClient:
      this.props.organization.client_for_email_signup ||
      this.props.clients[0].id,
  };

  _updateField = (state) => this.setState(_.extend({needsSave: true}, state));
  onDomainsChange = (domainObjects) =>
    this._updateField({domains: _.pluck(domainObjects, "name")});
  onClientSelect = (client) => this._updateField({signupClient: client.id});
  onChange = (stateField, value) => this._updateField({[stateField]: value});

  _checkErrors = () => {
    this.setState({error: null});
    if (this.state.allowSignupLink && _.isEmpty(this.state.domains)) {
      return Promise.reject(
        new NetError({
          message:
            "You must specify at least one email domain to create a Sign Up link.",
          status: 400,
        }),
      );
    } else {
      return Promise.resolve(null);
    }
  };

  onSave = () =>
    this._checkErrors().then(() =>
      this.props.promiseApiClient
        .organizations(this.props.organization.id)
        .update({
          allow_signup_from_email_domains: this.state.allowSignupLink,
          client_for_email_signup: this.state.signupClient,
          email_domains: this.state.domains,
        }),
    );

  onRotate = () => {
    this.setState({rotated: true});
    this.onSave().then(refreshPage, this.onError);
  };

  onError = (error) => {
    if (_.contains([400, 403], error.status)) {
      this.setState({error});
      error.handle();
    }
  };

  render() {
    const eligibleEmails = _.chain(this.props.organization.email_domains)
      .concat(
        _.map(this.props.memberships, (m) =>
          extractDomainFromEmail(m.user.email),
        ),
      )
      .concat(_.map(this.props.invites, (i) => extractDomainFromEmail(i.email)))
      .unique()
      .map((d) => ({name: d}))
      .value();

    const signupLinkIsValid =
      this.props.signupToken &&
      this.props.organization.client_for_email_signup ===
        this.state.signupClient &&
      !this.state.rotated;
    const signupUrl = new Url(this.props.appUrl);
    signupUrl.path = "/signup";
    signupUrl.params = {
      token: this.props.signupToken && this.props.signupToken.token,
    };
    const signupLink = signupUrl.toString();

    return (
      <div className="invite-permissions-section">
        <Control label="Allowed Domains">
          <p>
            You can list email domains below, and only users with emails
            belonging to those domains will be permitted to join. Existing users
            will be unaffected. Leave empty to allow any domain.
          </p>
          <Typeahead
            allowNew={true}
            className="allowed-domains-input"
            id="domains-input"
            labelKey="name"
            multiple={true}
            newSelectionPrefix="Add a domain: "
            onChange={this.onDomainsChange}
            options={eligibleEmails}
            selected={_.map(this.state.domains, (d) => ({name: d}))}
          />
        </Control>
        <label>Sign Up Methods</label>
        <RadioControl
          checked={!this.state.allowSignupLink}
          label="Require Invite"
          name="logintype"
          onChange={() => this._updateField({allowSignupLink: false})}
          {...this.state}
        />
        <RadioControl
          checked={this.state.allowSignupLink}
          label="Enable Sign Up Link"
          name="logintype"
          onChange={() => this._updateField({allowSignupLink: true})}
          {...this.state}
        />
        {this.state.allowSignupLink ? (
          <InputGroup title="Sign Up Link">
            <p>
              Generate a secret link that will allow users to sign up for{" "}
              {PRODUCT_NAME}
              and join your Organization without inviting them manually. Users
              will be required to verify an email belonging to one of the
              domains listed above.
            </p>
            <DefaultTeamControl
              clients={this.props.clients}
              onClientSelect={this.onClientSelect}
              signupClient={this.state.signupClient}
            />
            {this.state.allowSignupLink ? (
              <ReadOnlyControl
                label="Secret Sign Up Link"
                value={
                  signupLinkIsValid
                    ? signupLink
                    : "Click Save to generate your link"
                }
              >
                <RotateInputButton
                  disabled={!signupLinkIsValid}
                  loginState={this.props.loginState}
                  promiseApiClient={this.props.promiseApiClient}
                  success={this.props.onRotate}
                  token={this.props.signupToken}
                />
              </ReadOnlyControl>
            ) : null}
          </InputGroup>
        ) : null}
        {this.state.error ? (
          <div className="alert alert-danger">{this.state.error.message}</div>
        ) : null}
        <ActionButton
          className="save-button"
          disabled={!this.state.needsSave}
          error={this.onError}
          onClick={this.onSave}
          success={refreshPage}
        >
          Save
        </ActionButton>
      </div>
    );
  }
}

const createInviteRelation = (invite) => ({
  email: invite.email,
  invite,
  owner: invite.membership_type === "owner",
  permissionMap: _.indexBy(invite.pending_permissions, "client"),
});

class OrganizationUserManagementPage extends React.Component {
  constructor(...args) {
    super(...args);
    this.state = {
      userRelationMap: _.chain([
        _.map(this.props.invites, createInviteRelation),
        _.map(this.props.memberships, (membership) => {
          const owner = membership.type === "owner";
          return {
            email: membership.user.email,
            membership,
            owner,
            permissionMap: owner
              ? {}
              : _.chain(this.props.permissions)
                  .filter((p) => p.email === membership.user.email)
                  .indexBy("client")
                  .value(),
          };
        }),
      ])
        .flatten(true)
        .indexBy("email")
        .value(),
    };
    this._invitesTable = React.createRef();
    this._membershipsTable = React.createRef();
    this._editTeamsModal = React.createRef();
    this._createInviteModal = React.createRef();
  }

  refreshPages = () => {
    if (this._invitesTable.current) {
      this._invitesTable.current.getInstance().reload();
    }
    this._membershipsTable.current.getInstance().reload();
  };

  modifyUserPermissions = (email, updater) => {
    this.setState(
      (prevState) => {
        const userRelationMap = _.extend({}, prevState.userRelationMap);
        const userRelation = userRelationMap[email];
        const updatedRelation = userRelation
          ? userRelation
          : {
              email,
              invite: {
                email,
                membership_type: "member",
                object: "invite",
                organization: this.props.organization.id,
                organization_name: this.props.organization.name,
                pending_permissions: [],
              },
              fresh: true,
              owner: false,
            };
        updatedRelation.permissionMap = _.extend(
          {},
          updatedRelation.permissionMap,
        );
        updater(updatedRelation.permissionMap);
        userRelationMap[email] = updatedRelation;
      },
      () => this.refreshPages(),
    );
  };

  upsertPermission = (permission) => {
    this.modifyUserPermissions(
      permission.email,
      (permissionMap) => (permissionMap[permission.client] = permission),
    );
  };

  deletePermission = (clientId, email) => {
    this.modifyUserPermissions(email, (permissionMap) => {
      delete permissionMap[clientId];
    });
  };

  onInviteCreate = (email, membership_type, client_invites) =>
    this.props.promiseApiClient
      .organizations(this.props.organization.id)
      .invites()
      .create({email, membership_type, client_invites})
      .then((invite) => {
        this.setState(
          (prevState) => {
            const userRelationMap = _.extend({}, prevState.userRelationMap);
            userRelationMap[email] = createInviteRelation(invite);
            userRelationMap[email].fresh = true;
            return {userRelationMap};
          },
          () => this.refreshPages(),
        );
        return invite;
      });

  onPermissionChange = (clientId, email, role, oldRole) => {
    if (role === InviteRoles.NO_ROLE) {
      return this.props.promiseApiClient
        .clients(clientId)
        .invites()
        .delete({email})
        .then((empty) => {
          this.deletePermission(clientId, email);
          return empty;
        });
    } else {
      return this.props.promiseApiClient
        .clients(clientId)
        .invites()
        .create({
          email: email,
          role: role,
          old_role: oldRole,
        })
        .then((newPermission) => {
          this.upsertPermission(newPermission);
          return newPermission;
        });
    }
  };

  onUninvite = (email) =>
    this.props.promiseApiClient
      .organizations(this.props.organization.id)
      .invites()
      .delete({email})
      .then((empty) => {
        this.setState(
          (prevState) => {
            const userRelationMap = _.extend({}, prevState.userRelationMap);
            delete userRelationMap[email];
            return {userRelationMap};
          },
          () => {
            this.props.alertBroker.info(
              `${email} has been uninvited from ${this.props.organization.name}`,
            );
            this.refreshPages();
          },
        );
        return empty;
      });

  openEditModal = (...args) => {
    this._editTeamsModal.current.open(...args);
  };

  render() {
    const clientMap = _.indexBy(this.props.clients, "id");
    const memberships = _.chain(this.state.userRelationMap)
      .filter("membership")
      .indexBy("email")
      .value();
    const invites = _.chain(this.state.userRelationMap)
      .filter("invite")
      .indexBy("email")
      .value();

    return (
      <div>
        <div className="invite-user">
          <button
            className="btn btn-primary toggle-button"
            onClick={
              this._createInviteModal.current
                ? this._createInviteModal.current.show
                : null
            }
            type="button"
          >
            Invite User Manually
          </button>
        </div>
        <EditTeamsModal
          alertBroker={this.props.alertBroker}
          clientMap={clientMap}
          currentUser={this.props.currentUser}
          ref={this._editTeamsModal}
          onPermissionChange={this.onPermissionChange}
          onUninvite={this.onUninvite}
        />
        {this.props.canInviteOwners ? (
          <CreateInviteOwnerModal
            alertBroker={this.props.alertBroker}
            appUrl={this.props.appUrl}
            clientMap={clientMap}
            ref={this._createInviteModal}
            onInviteCreate={this.onInviteCreate}
            organization={this.props.organization}
          />
        ) : (
          <CreateInviteAdminModal
            alertBroker={this.props.alertBroker}
            clientMap={clientMap}
            onPermissionChange={this.onPermissionChange}
            organization={this.props.organization}
            ref={this._createInviteModal}
            usedEmails={_.keys(this.state.userRelationMap)}
          />
        )}
        {!_.isEmpty(invites) && (
          <div className="invites-section">
            <MembershipTable
              alertBroker={this.props.alertBroker}
              canInviteOwners={this.props.canInviteOwners}
              clients={this.props.clients}
              currentUser={this.props.currentUser}
              legacyApiClient={this.props.legacyApiClient}
              onUninvite={this.onUninvite}
              openEditModal={this.openEditModal}
              organization={this.props.organization}
              pageSize={3}
              promiseApiClient={this.props.promiseApiClient}
              ref={this._invitesTable}
              tableType={TableType.Invite}
              userRelationMap={invites}
            />
          </div>
        )}
        <div className="memberships-section">
          <MembershipTable
            alertBroker={this.props.alertBroker}
            canInviteOwners={this.props.canInviteOwners}
            clients={this.props.clients}
            currentUser={this.props.currentUser}
            legacyApiClient={this.props.legacyApiClient}
            onUninvite={this.onUninvite}
            openEditModal={this.openEditModal}
            organization={this.props.organization}
            pageSize={10}
            promiseApiClient={this.props.promiseApiClient}
            ref={this._membershipsTable}
            tableType={TableType.Membership}
            userRelationMap={memberships}
          />
        </div>
        {this.props.canInviteOwners ? (
          <div className="permissions-section">
            <h3>Permissions</h3>
            <SignupPermissionsEditor
              alertBroker={this.props.alertBroker}
              appUrl={this.props.appUrl}
              clients={this.props.clients}
              invites={this.props.invites}
              loginState={this.props.loginState}
              memberships={this.props.memberships}
              organization={this.props.organization}
              promiseApiClient={this.props.promiseApiClient}
              signupToken={this.props.signupToken}
            />
          </div>
        ) : null}
      </div>
    );
  }
}

export default function OrganizationUsersPage(props) {
  return (
    <OrganizationDashboardPage className="admin-page" {...props}>
      <OrganizationUserManagementPage {...props} />
    </OrganizationDashboardPage>
  );
}
