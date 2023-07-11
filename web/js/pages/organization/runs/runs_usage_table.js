/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import {get as lodashGet} from "lodash";

import Header from "../../../table/header";
import PagingBlock from "../../../pagination/paging-block";
import PagingTable from "../../../pagination/paging-table";
import Tooltip from "../../../component/tooltip";
import arrayPager from "../../../net/list";
import makePageable from "../../../pagination/make-pageable";
import {RelativeTime} from "../../../render/format_times";
import {isUndefinedOrNull} from "../../../utils";

export const RunsUsageTableObjects = {
  USER: "USER",
  TEAM: "TEAM",
};

const DEFAULT_PAGE_SIZE = 10;
const dataFetcher = function (...args) {
  const rows = this.props.rowData || [];

  let sortedRows;
  if (this.state.sortKey.includes(".")) {
    sortedRows = _.sortBy(rows, (row) => lodashGet(row, this.state.sortKey));
  } else {
    sortedRows = _.sortBy(rows, this.state.sortKey);
  }

  return arrayPager(sortedRows.reverse(), DEFAULT_PAGE_SIZE)(...args);
};
export const RunsUsageTable = makePageable(
  dataFetcher,
  class RunsUsageTable extends React.Component {
    static propTypes = {
      data: PropTypes.arrayOf(PropTypes.object),
      id: PropTypes.string,
      objectType: PropTypes.string,
      pageSize: PropTypes.number,
      rowData: PropTypes.arrayOf(PropTypes.object),
      setSortAscending: PropTypes.func.isRequired,
      sortAscending: PropTypes.bool,
      team: PropTypes.string,
      timePeriods: PropTypes.arrayOf(PropTypes.object),
    };

    static defaultProps = {
      pageSize: DEFAULT_PAGE_SIZE,
    };

    constructor(props) {
      super(props);
      if (!RunsUsageTableObjects[props.objectType]) {
        throw new Error("Unsupported object type");
      }

      this.state = {
        sortKey: "timePeriods.Total.count",
      };
    }

    onSort = (sortKey, sortAscending) => {
      this.props.setSortAscending(sortAscending);
      this.setState({sortKey: sortKey});
    };

    renderUserRow = (user) => {
      const teamNames = _.pluck(user.clients, "name");
      const userURL = `/organization/${user.organization.id}/users/${user.id}`;
      return (
        <tr key={user.id}>
          <td className="fixed-lg-column">
            <a href={userURL}>{user.name}</a>
          </td>
          <td className="fixed-md-column right-align">
            <Tooltip tooltip={`${teamNames.join(", ")}`}>
              {" "}
              {user.clients.length}{" "}
            </Tooltip>
          </td>
          {_.map(this.props.timePeriods, (timePeriod, i) => {
            const classes = "fixed-md-column right-align";
            return (
              <td className={classes} key={i}>
                {user.timePeriods[timePeriod.label].count}
              </td>
            );
          })}
          <td className="right-align">
            {isUndefinedOrNull(user.lastRun) ? (
              "-"
            ) : (
              <RelativeTime time={user.lastRun.created} />
            )}
          </td>
        </tr>
      );
    };

    renderTeamRow = (client) => (
      <tr key={client.id}>
        <td className="fixed-lg-column">{client.name}</td>
        <td className="fixed-md-column right-align">{client.users.length}</td>
        {_.map(this.props.timePeriods, (timePeriod, i) => {
          const classes = "fixed-md-column right-align";
          return (
            <td className={classes} key={i}>
              {client.timePeriods[timePeriod.label].count}
            </td>
          );
        })}
        <td />
      </tr>
    );

    render() {
      const isUsersTable = this.props.objectType === RunsUsageTableObjects.USER;
      const isTeamsTable = this.props.objectType === RunsUsageTableObjects.TEAM;

      const userSpecificHeaders = {
        numTeamsHeader: (
          <Header
            active={this.state.sortKey === "clients.length"}
            onClick={this.onSort}
            sortAscending={this.props.sortAscending}
            sortKey="clients.length"
            sortable={true}
            title="Number of Teams"
            className="fixed-md-column right-align"
          >
            # of Teams
          </Header>
        ),
        lastRunHeader: (
          <Header
            active={this.state.sortKey === "lastRun.created"}
            onClick={this.onSort}
            sortAscending={this.props.sortAscending}
            sortKey="lastRun.created"
            sortable={true}
            title="Last Run"
            className="flex-column right-align"
          >
            Last Run
          </Header>
        ),
      };

      const teamSpecificHeaders = {
        numUsersHeader: (
          <Header
            active={this.state.sortKey === "users.length"}
            onClick={this.onSort}
            sortAscending={this.props.sortAscending}
            sortKey="users.length"
            sortable={true}
            title="Number of Users"
            className="fixed-md-column right-align"
          >
            # of Users
          </Header>
        ),
      };

      const tableHeaders = (
        <thead>
          <tr>
            <td className="fixed-lg-column" />
            <td className="fixed-md-column" />
            <td className="experiment-usage-header" colSpan={4}>
              Runs Usage
            </td>
          </tr>
          <tr className="header-columns">
            <Header
              active={this.state.sortKey === "name"}
              onClick={this.onSort}
              sortAscending={this.props.sortAscending}
              sortKey="name"
              sortable={true}
              title="Name"
              className="fixed-lg-column"
            >
              Name
            </Header>
            {isUsersTable ? userSpecificHeaders.numTeamsHeader : null}
            {isTeamsTable ? teamSpecificHeaders.numUsersHeader : null}
            {_.map(this.props.timePeriods, (timePeriod, i) => {
              const sortKey = `timePeriods.${timePeriod.label}.count`;
              let borderClass = "";
              if (i === 0) {
                borderClass = "left-border";
              }
              if (i === this.props.timePeriods.length - 1) {
                borderClass += " right-border";
              }
              return (
                <Header
                  key={i}
                  active={this.state.sortKey === sortKey}
                  onClick={this.onSort}
                  sortAscending={this.props.sortAscending}
                  sortKey={sortKey}
                  sortable={true}
                  title={timePeriod.label}
                  className={`right-align fixed-md-column ${borderClass}`}
                >
                  {timePeriod.label}
                </Header>
              );
            })}
            {isUsersTable ? userSpecificHeaders.lastRunHeader : null}
          </tr>
        </thead>
      );

      return (
        <div id={this.props.id} className="usage-table sortable-table">
          <PagingTable className="table" head={tableHeaders} {...this.props}>
            {this.props.data && this.props.data.length === 0
              ? "There aren't any!"
              : null}
            {isUsersTable ? _.map(this.props.data, this.renderUserRow) : null}
            {isTeamsTable ? _.map(this.props.data, this.renderTeamRow) : null}
          </PagingTable>
          <PagingBlock {...this.props} />
        </div>
      );
    }
  },
);
