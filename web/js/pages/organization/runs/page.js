/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../styles/less/organization/experiments.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ClientsDropdown from "../../../client/dropdown";
import OrganizationDashboardPage from "../page_wrapper";
import RunsUsage from "./runs_usage";
import Spinner from "../../../component/spinner";
import schemas from "../../../react/schemas";
import {RunsUsageTable, RunsUsageTableObjects} from "./runs_usage_table";
import {
  calculateLastNPeriods,
  getCurrentPeriodEnd,
  getTimePeriodLabel,
} from "../../../time";
import {
  createTeamRunsUsageSourcePool,
  fetchTeamsRunsUsageData,
} from "./async_team_usage";
import {
  createUserRunsUsageSourcePool,
  fetchUsersRunsUsageData,
} from "./async_user_usage";
import {isDefinedAndNotNull, isUndefinedOrNull} from "../../../utils";
import {usersWithClients} from "../../../user/helpers";

const runsThisPeriodLabel = (optimized) => {
  const optimized_label = optimized ? "Optimized" : "All";
  const period_label = "month";
  return `${optimized_label} Runs this ${period_label}`;
};

const teamsFromClientsAndUsers = function (clients, users) {
  const teams = clients;

  _.each(teams, (team) => {
    const teamUsers = _.filter(users, (user) => {
      const userClientIds = _.pluck(user.clients, "id");
      return _.contains(userClientIds, team.id);
    });
    team.users = teamUsers;
  });

  return _.sortBy(teams, (t) => t.name.toLowerCase());
};

class OrganizationRunsManagementPage extends React.Component {
  static propTypes = {
    clients: PropTypes.arrayOf(schemas.Client.isRequired).isRequired,
    memberships: PropTypes.arrayOf(schemas.Membership.isRequired).isRequired,
    organization: schemas.Organization.isRequired,
    permissions: PropTypes.arrayOf(schemas.Permission.isRequired).isRequired,
    promiseApiClient: PropTypes.object.isRequired,
  };
  static displayName = "OrganizationRunsManagementPage";

  constructor(props) {
    super(props);

    const currentPeriodEnd = getCurrentPeriodEnd();
    const lastNPeriods = calculateLastNPeriods(3, currentPeriodEnd);
    const timePeriods = Object.freeze([
      ...lastNPeriods,
      {start: null, end: null, label: "Total"},
    ]);
    const users = usersWithClients(props.memberships, props.permissions);
    const teams = teamsFromClientsAndUsers(props.clients, users);
    let optimized = true;
    const usersOptimizedUsageDataPool = createUserRunsUsageSourcePool(
      this.props.organization.id,
      this.props.promiseApiClient,
      optimized,
    );
    const usersAllRunsUsageDataPool = createUserRunsUsageSourcePool(
      this.props.organization.id,
      this.props.promiseApiClient,
    );
    optimized = true;
    const teamsOptimizedUsageDataPool = createTeamRunsUsageSourcePool(
      this.props.promiseApiClient,
      optimized,
    );

    this.state = {
      client:
        _.size(this.props.clients) > 1 ? null : _.first(this.props.clients),
      clients: _.sortBy(this.props.clients, (c) => c.name.toLowerCase()),
      currentPeriodEnd,
      users,
      teams,
      usersOptimizedUsageDataPool,
      usersAllRunsUsageDataPool,
      usersTableRowsAllRuns: null,
      usersTableRowsOptRuns: null,
      teamsOptimizedUsageDataPool,
      teamsTableRows: null,
      timePeriods,
    };
  }

  static getDerivedStateFromProps(props) {
    return {
      clients: _.sortBy(props.clients, (c) => c.name.toLowerCase()),
    };
  }

  componentDidMount() {
    this.fetchUsersTableData();
    this.fetchTeamsTableData();
  }

  validate_api_use(
    optimized_user_table_runs,
    organization_optimized_runs_in_billing_cycle,
  ) {
    const last_month_add_value = _.reduce(
      optimized_user_table_runs,
      (sum, new_row) => {
        // look for the last time period
        const month = new Date().toLocaleString("en-US", {month: "short"});
        const lastMonthValue = new_row.timePeriods[month]?.count ?? 0;
        return sum + lastMonthValue;
      },
      0,
    );

    return (
      organization_optimized_runs_in_billing_cycle !== last_month_add_value
    );
  }

  fetchUsersTableData() {
    const getTeamFilterId = (client) =>
      isDefinedAndNotNull(client) ? client.id : client;
    const teamFilterId = getTeamFilterId(this.state.client);

    let users = this.state.users;
    if (teamFilterId) {
      users = _.filter(this.state.users, (user) => {
        const teamIds = _.pluck(user.clients, "id");
        return _.contains(teamIds, teamFilterId);
      });
    }

    const userIds = _.values(_.pluck(users, "id"));
    fetchUsersRunsUsageData(
      this.state.usersAllRunsUsageDataPool,
      userIds,
      teamFilterId,
      this.state.timePeriods,
    ).then((usersUsageData) => {
      this.setState((prevState) => {
        const currentTeamFilterId = getTeamFilterId(prevState.client);
        if (currentTeamFilterId === teamFilterId) {
          const usersTableRowsAllRuns = _.map(users, (user) =>
            _.extend(_.clone(user), usersUsageData[user.id]),
          );
          return {usersTableRowsAllRuns};
        }
        return undefined;
      });
    });

    fetchUsersRunsUsageData(
      this.state.usersOptimizedUsageDataPool,
      userIds,
      teamFilterId,
      this.state.timePeriods,
    ).then((usersUsageData) => {
      this.setState((prevState) => {
        const currentTeamFilterId = getTeamFilterId(prevState.client);
        if (currentTeamFilterId === teamFilterId) {
          const usersTableRowsOptRuns = _.map(users, (user) =>
            _.extend(_.clone(user), usersUsageData[user.id]),
          );
          return {usersTableRowsOptRuns};
        }
        return undefined;
      });
    });
  }

  fetchTeamsTableData() {
    const teamIds = _.values(_.pluck(this.state.teams, "id"));
    fetchTeamsRunsUsageData(
      this.state.teamsOptimizedUsageDataPool,
      teamIds,
      this.state.timePeriods,
    ).then((teamsUsageData) => {
      this.setState((prevState) => {
        const teamsTableRows = _.map(prevState.teams, (team) =>
          _.extend(_.clone(team), teamsUsageData[team.id]),
        );
        return {teamsTableRows};
      });
    });
  }

  filterClient(client) {
    if (this.state.client !== client) {
      this.setState(
        {
          client: client,
          usersTableRowsAllRuns: null,
        },
        () => {
          this.fetchUsersTableData();
          this._recentExperimentsTable.getInstance().reload();
        },
      );
    }
  }

  render() {
    const moreThanOneClient = this.state.clients.length > 1;
    const numUsers = this.props.memberships.length;
    const numTeams = this.state.clients.length;

    return (
      <>
        <div className="experiments-info">
          <div>
            <div className="row">
              <div className="period">
                <h3>Current usage period</h3>
                <div className="data">{getTimePeriodLabel()}</div>
              </div>
            </div>
            <div className="row">
              <div className="org-info-runs">
                <div className="data">
                  {this.props.organization.total_runs_in_billing_cycle}
                </div>
                <span className="static-label">
                  {runsThisPeriodLabel(false)}
                </span>
              </div>
              <div className="org-info-runs">
                <div className="data">
                  {this.props.organization.optimized_runs_in_billing_cycle}
                </div>
                <span className="static-label">
                  {runsThisPeriodLabel(true)}
                </span>
              </div>
              <div className="org-info-runs">
                <div className="data">{numTeams}</div>
                <span className="static-label">Teams</span>
              </div>
              <div className="org-info-runs">
                <div className="data">{numUsers}</div>
                <span className="static-label">Users</span>
              </div>
            </div>
          </div>
        </div>

        <RunsUsage
          promiseApiClient={this.props.promiseApiClient}
          currentPeriodEnd={this.state.currentPeriodEnd}
          organization={this.props.organization}
        />
        <div>
          <h3>Users</h3>
          {moreThanOneClient ? (
            <div className="form-group client-filter">
              <label className="control-label">Filter by team:</label>
              <ClientsDropdown
                allowBlank={true}
                blankLabel="All"
                clients={this.state.clients}
                onClientSelect={(client) => this.filterClient(client)}
                selectedClient={this.state.client}
              />
            </div>
          ) : null}
        </div>
        <h3>All Runs</h3>
        {isUndefinedOrNull(this.state.usersTableRowsAllRuns) ? (
          <Spinner />
        ) : (
          <RunsUsageTable
            rowData={this.state.usersTableRowsAllRuns}
            objectType={RunsUsageTableObjects.USER}
            timePeriods={this.state.timePeriods}
            id="users-all-runs-table"
          />
        )}

        <h3>Only Optimized Runs</h3>
        {isUndefinedOrNull(this.state.usersTableRowsOptRuns) ? (
          <Spinner />
        ) : (
          <RunsUsageTable
            rowData={this.state.usersTableRowsOptRuns}
            objectType={RunsUsageTableObjects.USER}
            timePeriods={this.state.timePeriods}
            id="users-optimized-only-table"
          />
        )}
        {moreThanOneClient ? (
          <div>
            <h3>Teams Optimized Runs</h3>
            {isUndefinedOrNull(this.state.teamsTableRows) ? (
              <Spinner />
            ) : (
              <RunsUsageTable
                rowData={this.state.teamsTableRows}
                objectType={RunsUsageTableObjects.TEAM}
                timePeriods={this.state.timePeriods}
                id="teams-table"
              />
            )}
          </div>
        ) : null}
      </>
    );
  }
}

export default function OrganizationRunsPage(props) {
  return (
    <OrganizationDashboardPage className="admin-page" {...props}>
      <OrganizationRunsManagementPage {...props} />
    </OrganizationDashboardPage>
  );
}
