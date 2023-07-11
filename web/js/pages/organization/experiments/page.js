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
import Component from "../../../react/component";
import ExperimentUsage from "./experiment_usage";
import Loading from "../../../component/loading";
import OrganizationDashboardPage from "../page_wrapper";
import PagingBlock from "../../../pagination/paging-block";
import PagingTable from "../../../pagination/paging-table";
import Spinner from "../../../component/spinner";
import makePageable from "../../../pagination/make-pageable";
import schemas from "../../../react/schemas";
import ui from "../../../experiment/ui";
import {
  ExperimentsUsageTable,
  ExperimentsUsageTableObjects,
} from "./experiments_usage_table";
import {RelativeTime} from "../../../render/format_times";
import {
  calculateLastNPeriods,
  getCurrentPeriodEnd,
  getTimePeriodLabel,
  subtractOneMonthUnix,
} from "../../../time";
import {
  createTeamUsageSourcePool,
  fetchTeamsUsageData,
} from "./async_team_usage";
import {
  createUserUsageSourcePool,
  fetchUsersUsageData,
} from "./async_user_usage";
import {isDefinedAndNotNull, isUndefinedOrNull} from "../../../utils";
import {usersWithClients} from "../../../user/helpers";

class ExperimentTableRow extends React.Component {
  static propTypes = {
    clientMap: PropTypes.object.isRequired,
    experiment: schemas.Experiment.isRequired,
    membershipMap: PropTypes.object.isRequired,
    showClient: PropTypes.bool.isRequired,
  };

  render() {
    const e = this.props.experiment;
    const membership = this.props.membershipMap[e.user];
    return (
      <tr>
        <td>
          <a href={ui.getExperimentUrl(e)}>{e.name}</a>
        </td>
        <td>{isDefinedAndNotNull(e.parameters) ? e.parameters.length : 0}</td>
        <td>{(e.progress && e.progress.observation_count) || 0}</td>
        {this.props.showClient ? (
          <td>{this.props.clientMap[e.client].name}</td>
        ) : null}
        <td>{membership ? membership.user.name : "Unknown"}</td>
        <td>{<RelativeTime time={e.updated} />}</td>
      </tr>
    );
  }
}

const experimentsFetcher = function (...args) {
  const currentPeriodExperimentsParams = {
    period_start: Math.floor(subtractOneMonthUnix(this.props.currentPeriodEnd)),
    period_end: Math.floor(this.props.currentPeriodEnd),
    development: false,
    include_ai: true,
  };
  if (isDefinedAndNotNull(this.props.client)) {
    return ((paging, success, error) =>
      this.props.promiseApiClient
        .clients(this.props.client.id)
        .experiments()
        .fetch(_.extend(paging, currentPeriodExperimentsParams))
        .then(success, error))(...args);
  } else {
    return ((paging, success, error) =>
      this.props.promiseApiClient
        .organizations(this.props.organization.id)
        .experiments()
        .fetch(_.extend(paging, currentPeriodExperimentsParams))
        .then(success, error))(...args);
  }
};
const RecentExperimentsTable = makePageable(
  experimentsFetcher,
  class RecentExperimentsTable extends React.Component {
    static propTypes = {
      client: schemas.Client,
      clients: PropTypes.arrayOf(schemas.Client.isRequired).isRequired,
      currentPeriodEnd: PropTypes.number.isRequired,
      data: PropTypes.arrayOf(schemas.Experiment),
      memberships: PropTypes.arrayOf(schemas.Membership.isRequired).isRequired,
      organization: schemas.Organization.isRequired,
      promiseApiClient: PropTypes.object.isRequired,
      reloadPages: PropTypes.func.isRequired,
    };

    static defaultProps = {
      emptyState: <p>There aren&rsquo;t any!</p>,
      pageSize: 10,
    };

    constructor(props) {
      super(props);
      const membershipMap = _.indexBy(this.props.memberships, (m) => m.user.id);
      const clientMap = _.indexBy(this.props.clients, (c) => c.id);
      this.state = {
        clientMap,
        membershipMap,
      };
    }

    reload() {
      this.props.reloadPages();
    }

    render() {
      return (
        <div>
          <h3>
            Experiments this month
            {this.props.client ? ` for team: ${this.props.client.name}` : null}
          </h3>
          <div className="table-responsive recent-experiments-table">
            <PagingTable
              className="table"
              head={
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Parameters</th>
                    <th>Observations</th>
                    {!isDefinedAndNotNull(this.props.client) && <th>Team</th>}
                    <th>Created By</th>
                    <th>Last Updated</th>
                  </tr>
                </thead>
              }
              {...this.props}
            >
              {_.map(this.props.data, (experiment) => (
                <ExperimentTableRow
                  key={experiment.id}
                  clientMap={this.state.clientMap}
                  experiment={experiment}
                  membershipMap={this.state.membershipMap}
                  showClient={!isDefinedAndNotNull(this.props.client)}
                />
              ))}
            </PagingTable>
            <div>
              <PagingBlock {...this.props} />
            </div>
          </div>
        </div>
      );
    }
  },
);

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

class CurrentMonthExperimentCount extends Component {
  state = {count: null};

  componentDidMount() {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    this.services.promiseApiClient
      .organizations(this.props.organization.id)
      .experiments()
      .fetch({
        limit: 0,
        period_start: Math.floor(startOfMonth / 1000),
      })
      .then(({count}) => this.setState({count}));
  }

  render() {
    return (
      <Loading loading={isUndefinedOrNull(this.state.count)}>
        {this.state.count}
      </Loading>
    );
  }
}

class OrganizationExperimentManagementPage extends React.Component {
  static propTypes = {
    clients: PropTypes.arrayOf(schemas.Client.isRequired).isRequired,
    memberships: PropTypes.arrayOf(schemas.Membership.isRequired).isRequired,
    organization: schemas.Organization.isRequired,
    permissions: PropTypes.arrayOf(schemas.Permission.isRequired).isRequired,
    promiseApiClient: PropTypes.object.isRequired,
  };
  static displayName = "OrganizationExperimentManagementPage";

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
    const usersUsageDataPool = createUserUsageSourcePool(
      this.props.organization.id,
      this.props.promiseApiClient,
    );
    const teamsUsageDataPool = createTeamUsageSourcePool(
      this.props.promiseApiClient,
    );

    this.state = {
      client:
        _.size(this.props.clients) > 1 ? null : _.first(this.props.clients),
      clients: _.sortBy(this.props.clients, (c) => c.name.toLowerCase()),
      currentPeriodEnd,
      users,
      teams,
      usersUsageDataPool,
      usersTableRows: null,
      teamsUsageDataPool,
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
    fetchUsersUsageData(
      this.state.usersUsageDataPool,
      userIds,
      teamFilterId,
      this.state.timePeriods,
    ).then((usersUsageData) => {
      this.setState((prevState) => {
        const currentTeamFilterId = getTeamFilterId(prevState.client);
        if (currentTeamFilterId === teamFilterId) {
          const usersTableRows = _.map(users, (user) =>
            _.extend(_.clone(user), usersUsageData[user.id]),
          );
          return {usersTableRows};
        }
        return undefined;
      });
    });
  }

  fetchTeamsTableData() {
    const teamIds = _.values(_.pluck(this.state.teams, "id"));
    fetchTeamsUsageData(
      this.state.teamsUsageDataPool,
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
          usersTableRows: null,
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
              <div className="org-info">
                <div className="data">
                  <CurrentMonthExperimentCount
                    organization={this.props.organization}
                  />
                </div>
                <span className="static-label">Experiments this month</span>
              </div>
              <div className="org-info">
                <div className="data">{numTeams}</div>
                <span className="static-label">Teams</span>
              </div>
              <div className="org-info">
                <div className="data">{numUsers}</div>
                <span className="static-label">Users</span>
              </div>
            </div>
          </div>
        </div>

        <ExperimentUsage
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
        {isUndefinedOrNull(this.state.usersTableRows) ? (
          <Spinner />
        ) : (
          <ExperimentsUsageTable
            rowData={this.state.usersTableRows}
            objectType={ExperimentsUsageTableObjects.USER}
            timePeriods={this.state.timePeriods}
            id="users-table"
          />
        )}

        <h3>Teams</h3>
        {isUndefinedOrNull(this.state.teamsTableRows) ? (
          <Spinner />
        ) : (
          <ExperimentsUsageTable
            rowData={this.state.teamsTableRows}
            objectType={ExperimentsUsageTableObjects.TEAM}
            timePeriods={this.state.timePeriods}
            id="teams-table"
          />
        )}

        <RecentExperimentsTable
          ref={(c) => {
            this._recentExperimentsTable = c;
          }}
          promiseApiClient={this.props.promiseApiClient}
          client={this.state.client}
          clients={this.state.clients}
          currentPeriodEnd={this.state.currentPeriodEnd}
          memberships={this.props.memberships}
          organization={this.props.organization}
        />
      </>
    );
  }
}

export default function OrganizationExperimentsPage(props) {
  return (
    <OrganizationDashboardPage className="admin-page" {...props}>
      <OrganizationExperimentManagementPage {...props} />
    </OrganizationDashboardPage>
  );
}
