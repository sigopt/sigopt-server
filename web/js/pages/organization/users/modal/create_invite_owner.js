/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import ReactDOMServer from "react-dom/server";

import Alert from "../../../../alert/alert";
import ModalForm from "../../../../component/modal/form";
import Tooltip from "../../../../component/tooltip";
import Url from "../../../../net/url";
import schemas from "../../../../react/schemas";
import {FooterTypes} from "../../../../component/modal/constant";
import {PermissionsEditor} from "../permissions_editor/editor";

export class CreateInviteOwnerModal extends React.Component {
  static propTypes = {
    alertBroker: schemas.AlertBroker.isRequired,
    appUrl: PropTypes.string.isRequired,
    clientMap: PropTypes.objectOf(schemas.Client).isRequired,
    onInviteCreate: PropTypes.func.isRequired,
    organization: schemas.Organization.isRequired,
  };

  static initialState = {
    addingPermission: true,
    email: "",
    ownerSelected: false,
    permissions: [],
  };

  constructor(...args) {
    super(...args);
    this.state = _.extend({}, CreateInviteOwnerModal.initialState);
    this._modal = React.createRef();
  }

  submitButtonLabel = "Create";
  submitable = true;
  showConfirm = false;

  isInputDisabled = () => this.state.ownerSelected || super.isInputDisabled();

  permissionsAreValid = () =>
    this.state.ownerSelected ||
    !(this.state.addingPermission || _.isEmpty(this.state.permissions));

  isValid = () => !_.isEmpty(this.state.email) && this.permissionsAreValid();

  show = () => {
    this._modal.current.clearAlerts();
    this.resetState();
    this._modal.current.clearAlerts();
    this._modal.current.show();
  };

  resetState = () => {
    this.setState(_.extend({}, CreateInviteOwnerModal.initialState));
  };

  onPermissionChange = (clientId, email, role) =>
    Promise.resolve({
      client: clientId,
      client_name: this.props.clientMap[clientId].name,
      email,
      role,
    });

  createInvite = (success, error) => {
    this.props
      .onInviteCreate(
        this.state.email,
        this.state.ownerSelected ? "owner" : "member",
        this.state.ownerSelected
          ? []
          : _.map(this.state.permissions, (p) => ({
              id: p.client,
              role: p.role,
            })),
      )
      .then((invite) => {
        const code = invite.invite_code;
        const email = invite.email;
        let url = null;
        if (code) {
          url = new Url(`${this.props.appUrl}/signup`);
          url.params = {
            code,
            email,
          };
        }
        this.props.alertBroker.handle(
          new Alert({
            type: "info",
            __htmlMessage: ReactDOMServer.renderToStaticMarkup(
              <>
                Created invitation for {email}.{" "}
                {url ? (
                  <>
                    {/*
                  HACK: Use <br/> tags here to avoid nesting <p> tags. Could refactor
                  AlertPanel to avoid this.
                */}
                    <br />
                    <br />
                    We emailed them, but you can also send the user to{" "}
                    <a href={url.toString()}>{url.toString()}</a> to accept
                    their invite.
                  </>
                ) : null}
              </>,
            ),
          }),
        );
        return invite;
      })
      .then(() => this.resetState())
      .then(success, (err) => {
        this.props.alertBroker.errorHandlerThatExpectsStatus(400, 403)(err);
        return error(err);
      });
  };

  render() {
    return (
      <div>
        <ModalForm
          footer={FooterTypes.SubmitAndCancel}
          hideOnSuccess={false}
          onSubmit={this.createInvite}
          ref={this._modal}
          submitButtonLabel="Invite"
          title={`Create an invitation to join ${this.props.organization.name}`}
          validator={this.isValid}
        >
          <span>
            <div className="email-input form-group">
              <label className="control-label">Email Address</label>
              <input
                className="form-control email"
                onChange={(e) => this.setState({email: e.target.value})}
                placeholder="user@domain.com"
                type="email"
                value={this.state.email || ""}
              />
            </div>
            <div className="owner-check form-group">
              <Tooltip
                tooltip={
                  "Organization owners will have full admin privileges to all" +
                  " of the teams in this organization"
                }
              >
                <label className="control-label btn-spacing">Owner</label>
              </Tooltip>
              <input
                type="checkbox"
                onChange={() =>
                  this.setState((prevState) => ({
                    ownerSelected: !prevState.ownerSelected,
                  }))
                }
                checked={this.state.ownerSelected}
              />
            </div>
            {this.state.ownerSelected || (
              <PermissionsEditor
                addingPermission={this.state.addingPermission}
                alertBroker={this.props.alertBroker}
                allowDeleteLast={true}
                clientMap={this.props.clientMap}
                disableInput={this.state.ownerSelected}
                email={this.state.email}
                onToggleAddingPermission={() =>
                  this.setState((prevState) => ({
                    addingPermission: !prevState.addingPermission,
                  }))
                }
                onPermissionChange={this.onPermissionChange}
                permissions={this.state.permissions}
                ref={this._permissionsEditor}
                showConfirm={true}
                updatePermissions={(permissions) =>
                  this.setState({permissions})
                }
              />
            )}
          </span>
        </ModalForm>
      </div>
    );
  }
}
