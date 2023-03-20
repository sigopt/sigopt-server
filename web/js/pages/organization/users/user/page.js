/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../../../../styles/less/organization/user_detail.less";

/* eslint-disable react/jsx-no-bind */
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";

import Page from "../../../../component/page";
import PaginatedTable from "../../../../pagination/paginated-table";
import VisibleBoolean from "../../../../render/boolean";
import schemas from "../../../../react/schemas";
import {RelativeTime} from "../../../../render/format_times";

const UserDetail = ({user}) => (
  <dl className="dl-horizontal">
    <dt>ID</dt>
    <dd>{user.id}</dd>
    <dt>Name</dt>
    <dd>{user.name}</dd>
    <dt>Email</dt>
    <dd>{user.email}</dd>
    <dt>Joined</dt>
    <dd>{user.created ? <RelativeTime time={user.created} /> : "-"}</dd>
    <dt>Has Verified Email</dt>
    <dd>
      <VisibleBoolean>{user.has_verified_email || false}</VisibleBoolean>
    </dd>
  </dl>
);

const ClientsTable = ({userPermissions}) => {
  const makeRow = (permission) => (
    <tr key={permission.client.id}>
      <td className="small-col">{permission.client && permission.client.id}</td>
      <td className="medium-col">
        {permission.client && permission.client.name}
      </td>
      <td className="small-col">{permission.can_admin ? "True" : "False"} </td>
      <td className="small-col">{permission.can_read ? "True" : "False"}</td>
      <td className="small-col">{permission.can_write ? "True" : "False"}</td>
    </tr>
  );
  const head = (
    <thead>
      <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Admin</th>
        <th>Read Privileges</th>
        <th>Write Privileges</th>
      </tr>
    </thead>
  );
  const permissions = _.sortBy(userPermissions, ({client}) => client.name);

  return <PaginatedTable allData={permissions} head={head} makeRow={makeRow} />;
};

export default class extends React.Component {
  static displayName = "UserDetailPage";

  static propTypes = {
    user: schemas.User.isRequired,
    userPermissions: PropTypes.arrayOf(schemas.Permission).isRequired,
  };

  render() {
    return (
      <Page loggedIn={true} className="org-admin-user-detail-page" title="User">
        <UserDetail user={this.props.user} />
        <h2>Teams</h2>
        <ClientsTable userPermissions={this.props.userPermissions} />
      </Page>
    );
  }
}
