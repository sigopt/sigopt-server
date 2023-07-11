/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/organization/teams.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Component from "../../../react/component";
import FieldEditor from "../../../component/fieldeditor";
import ModalForm from "../../../component/modal/form";
import OrganizationDashboardPage from "../page_wrapper";
import TriggerModalButton from "../../../component/modal/button";
import schemas from "../../../react/schemas";
import {FooterTypes} from "../../../component/modal/constant";
import {RelativeTime} from "../../../render/format_times";

class CreateTeamButton extends Component {
  static propTypes = {
    onCreate: PropTypes.func.isRequired,
    organization: schemas.Organization.isRequired,
  };

  state = {
    name: "",
  };

  render() {
    return (
      <TriggerModalButton className="btn btn-primary" label="Create Team">
        <ModalForm
          title="Create a new team"
          footer={FooterTypes.SubmitAndCancel}
          onSubmit={(success, error) =>
            this.services.promiseApiClient
              .organizations(this.props.organization.id)
              .clients()
              .create({
                name: this.state.name,
              })
              .then(
                (client) => {
                  this.props.onCreate(client);
                  return success && success();
                },
                (err) => {
                  this.services.alertBroker.errorHandlerThatExpectsStatus(
                    400,
                    403,
                  )(err);
                  return error && error(err);
                },
              )
          }
          submitButtonLabel="Create"
          validator={() => this.state.name.length > 0}
        >
          <label className="control-label">Name</label>
          <input
            className="form-control control-input"
            onChange={(e) => this.setState({name: e.target.value})}
            placeholder="Team name"
            type="text"
          />
        </ModalForm>
      </TriggerModalButton>
    );
  }
}

class OrganizationTeamManagementPage extends Component {
  state = {clients: this.props.clients};

  render() {
    const sortedClients = _.sortBy(this.state.clients, (c) =>
      c.name.toLowerCase(),
    );
    return (
      <div className="teams-page">
        <div className="section-button">
          {this.props.canCreateTeam ? (
            <CreateTeamButton
              onCreate={(client) => {
                this.services.alertBroker.info(
                  `Team ${client.name} was created successfully`,
                );
                this.setState((prevState) => ({
                  clients: [client].concat(prevState.clients),
                }));
              }}
              organization={this.props.organization}
            />
          ) : null}
        </div>
        <div className="section-title">
          <h3>Teams</h3>
        </div>
        <div className="section-content">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {_.map(sortedClients, (client) => (
                <tr data-id={client.id} key={client.id}>
                  <td>
                    <FieldEditor
                      alertBroker={this.services.alertBroker}
                      fieldName="name"
                      loginState={this.props.loginState}
                      updateFunction={
                        this.services.legacyApiClient.clientUpdate
                      }
                      object={client}
                    />
                  </td>
                  <td>
                    <RelativeTime time={client.created} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
}

export default function OrganizationTeamsPage(props) {
  return (
    <OrganizationDashboardPage className="admin-page" {...props}>
      <OrganizationTeamManagementPage {...props} />
    </OrganizationDashboardPage>
  );
}
