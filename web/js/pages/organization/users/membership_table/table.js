/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import ClientsDropdown from "../../../../client/dropdown";
import PagingBlock from "../../../../pagination/paging-block";
import PagingTable from "../../../../pagination/paging-table";
import Tooltip from "../../../../component/tooltip";
import arrayPager from "../../../../net/list";
import makePageable from "../../../../pagination/make-pageable";
import schemas from "../../../../react/schemas";
import {MembershipTableRow} from "./table_row";

export const TableType = {
  Membership: "membership",
  Invite: "invite",
};

const pageFetcher = function (...args) {
  return arrayPager(this.getFilteredUsers())(...args);
};

export const MembershipTable = makePageable(
  pageFetcher,
  class MembershipTable extends React.Component {
    static propTypes = {
      alertBroker: schemas.AlertBroker.isRequired,
      canInviteOwners: PropTypes.bool,
      clients: PropTypes.arrayOf(PropTypes.object.isRequired),
      currentUser: schemas.User.isRequired,
      data: PropTypes.arrayOf(PropTypes.object),
      onUninvite: PropTypes.func.isRequired,
      openEditModal: PropTypes.func.isRequired,
      pageSize: PropTypes.number.isRequired,
      reloadPages: PropTypes.func.isRequired,
      tableType: PropTypes.oneOf(_.values(TableType)).isRequired,
      userRelationMap: PropTypes.object.isRequired,
    };

    constructor(props) {
      super(props);
      this.state = {
        nameFilter: "",
        selectedClient:
          _.size(this.props.clients) === 1 ? _.first(this.props.clients) : null,
      };
    }

    reload() {
      this.props.reloadPages();
    }

    getUserPermissions(userEmail) {
      const userRelation = this.props.userRelationMap[userEmail];
      return (
        userRelation && _.sortBy(userRelation.permissionMap, "client_name")
      );
    }

    filterRelationsByClient(clientId) {
      const inviteRelations = _.filter(this.props.userRelationMap, "invite");
      const membershipRelations = _.filter(
        this.props.userRelationMap,
        "membership",
      );
      const clientFilter = clientId
        ? (relationList) =>
            _.filter(relationList, (r) => r.permissionMap[clientId])
        : (relationList) => _.filter(relationList, (r) => !r.owner);
      const sortedOwnerInvites = _.chain(inviteRelations)
        .filter("owner")
        .sortBy((i) => i.email.toLowerCase())
        .value();
      const sortedMemberInvites = _.sortBy(clientFilter(inviteRelations), (i) =>
        i.email.toLowerCase(),
      );
      const sortedOwnerMemberships = _.chain(membershipRelations)
        .filter("owner")
        .sortBy((i) => i.membership.user.name.toLowerCase())
        .value();
      const sortedMemberMemberships = _.sortBy(
        clientFilter(membershipRelations),
        (i) => i.membership.user.name.toLowerCase(),
      );
      return _.flatten(
        [
          sortedOwnerInvites,
          sortedMemberInvites,
          sortedOwnerMemberships,
          sortedMemberMemberships,
        ],
        true,
      );
    }

    getFilteredUsers() {
      const client = this.state.selectedClient;
      const userRelations = this.filterRelationsByClient(client && client.id);

      return _.size(this.state.nameFilter)
        ? _.filter(
            userRelations,
            (relation) =>
              (relation.membership &&
                relation.membership.user.name
                  .toLowerCase()
                  .includes(this.state.nameFilter)) ||
              relation.email.toLowerCase().includes(this.state.nameFilter),
          )
        : userRelations;
    }

    filterName(name) {
      this.setState({nameFilter: name.toLowerCase()}, () =>
        this.props.reloadPages(),
      );
    }

    filterClient(client) {
      this.setState({selectedClient: client}, () => this.props.reloadPages());
    }
    render() {
      const isForInvites = this.props.tableType === TableType.Invite;
      const className = isForInvites ? "invite" : "membership";
      const tooltipContent = (
        <span>
          <b>Owners</b> have full control of an organization and are
          automatically an admin on all teams. <b>Members</b> must be assigned
          roles to each team they are on.
        </span>
      );
      return (
        <div
          className="accordion membership-table"
          id="userTable"
          key="members"
        >
          <div className="table-search-row">
            <h3>{isForInvites ? "Invites" : "Users"}</h3>
            <div className="table-search-holder">
              <div className="filter-row">
                <label className="control-label filter-element">Viewing</label>
                <ClientsDropdown
                  allowBlank={true}
                  blankLabel={`All teams (${_.size(this.props.clients)})`}
                  buttonClassName="btn clients-dropdown-btn dropdown-toggle"
                  clients={this.props.clients}
                  onClientSelect={(client) => this.filterClient(client)}
                  selectedClient={this.state.selectedClient}
                />
              </div>
              <div className="filter-row">
                <label className="control-label filter-element">Filter</label>
                <input
                  className="name-filter form-control table-search filter-element"
                  placeholder="Search"
                  type="text"
                  onChange={(e) =>
                    _.throttle(this.filterName(e.target.value), 500)
                  }
                />
              </div>
              <div className="info-row">
                {_.size(this.getFilteredUsers())} of{" "}
                {_.size(this.props.userRelationMap)} total{" "}
                {isForInvites ? "invites" : "users"}
              </div>
            </div>
          </div>
          <div className="table-hover table-responsive">
            <PagingTable
              className="table"
              head={
                <thead>
                  <tr>
                    {isForInvites ? null : (
                      <th className="membership table-name-header">Name</th>
                    )}
                    <th className={`${className} table-email-header`}>Email</th>
                    <th className={`${className} table-type-header`}>
                      <Tooltip html={true} tooltip={tooltipContent}>
                        Type
                      </Tooltip>
                    </th>
                    <th className={`${className} table-teams-header`}>
                      # of Teams
                    </th>
                    <th />
                  </tr>
                </thead>
              }
              {...this.props}
            >
              {_.map(this.props.data, (userRelation) => {
                let clients = this.props.clients;
                if (!userRelation.owner) {
                  const clientMap = _.indexBy(this.props.clients, "id");
                  clients = _.map(
                    userRelation.permissionMap,
                    (p) => clientMap[p.client],
                  );
                }
                return (
                  <MembershipTableRow
                    alertBroker={this.props.alertBroker}
                    canInviteOwners={this.props.canInviteOwners}
                    clients={clients}
                    currentUser={this.props.currentUser}
                    key={userRelation.email}
                    onUninvite={this.props.onUninvite}
                    openEditModal={this.props.openEditModal}
                    renderName={this.props.tableType === TableType.Membership}
                    selectedClient={this.state.selectedClient}
                    userRelation={userRelation}
                  />
                );
              })}
            </PagingTable>
          </div>
          <PagingBlock {...this.props} />
        </div>
      );
    }
  },
);
