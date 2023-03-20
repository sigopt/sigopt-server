/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import CustomTooltip from "../../../../component/custom_tooltip";
import PencilGlyph from "../../../../component/glyph/pencil";
import XmarkGlyph from "../../../../component/glyph/xmark";
import schemas from "../../../../react/schemas";

export class MembershipTableRow extends React.Component {
  static propTypes = {
    canInviteOwners: PropTypes.bool.isRequired,
    clients: PropTypes.arrayOf(schemas.Client).isRequired,
    currentUser: schemas.User.isRequired,
    openEditModal: PropTypes.func.isRequired,
    renderName: PropTypes.bool.isRequired,
    userRelation: PropTypes.object.isRequired,
  };

  openEditModal() {
    this.props.openEditModal(this.props.userRelation, true);
  }

  openUninviteModal() {
    this.props.openEditModal(this.props.userRelation, false);
  }

  isMembership() {
    return Boolean(this.props.userRelation.membership);
  }

  getName() {
    return this.props.userRelation.membership.user.name;
  }

  isCurrentUserRow() {
    return this.props.userRelation.email === this.props.currentUser.email;
  }

  render() {
    const renderTeams = () => {
      const sortedClients = _.sortBy(this.props.clients, "name");
      const namesCount = _.size(sortedClients);
      if (namesCount === 0) {
        return <span>0</span>;
      } else {
        return (
          <div>
            <CustomTooltip tooltip={_.pluck(sortedClients, "name").join(", ")}>
              <span className="tooltip-trigger team-count default-cursor">
                {namesCount}
              </span>
            </CustomTooltip>
          </div>
        );
      }
    };

    const canEdit = this.isMembership() || !this.props.userRelation.owner;
    const userAllowedToUninvite =
      !this.isCurrentUserRow() && this.props.canInviteOwners;
    const ableToUninvite = this.isMembership()
      ? !this.props.userRelation.owner
      : true;
    const canUninvite = userAllowedToUninvite && ableToUninvite;

    const renderEditButton = () => {
      if (canEdit) {
        const editButton = (
          <a
            className={classNames(
              "edit-button btn btn-xs btn-remove btn-spacing",
              this.props.userRelation.owner
                ? "tooltip-trigger btn-disabled"
                : "",
            )}
            key="editButton"
            onClick={
              this.props.userRelation.owner ? null : () => this.openEditModal()
            }
          >
            <PencilGlyph />
          </a>
        );
        if (this.props.userRelation.owner) {
          return (
            <CustomTooltip
              hideDelay={0}
              showDelay={200}
              tooltip="Cannot edit an owner"
            >
              {editButton}
            </CustomTooltip>
          );
        } else {
          return editButton;
        }
      } else {
        return <span className="spacer" key="editSpace" />;
      }
    };

    const renderUninviteButton = () => {
      if (canUninvite) {
        return (
          <a
            className="uninvite-button btn btn-xs btn-remove btn-spacing"
            key="uninviteButton"
            onClick={() => this.openUninviteModal()}
          >
            <XmarkGlyph />
          </a>
        );
      } else {
        return <span className="spacer" key="uninviteSpace" />;
      }
    };

    let link = false;
    if (this.props.userRelation.membership) {
      const userId = this.props.userRelation.membership.user.id;
      const organizationId = this.props.userRelation.membership.organization.id;
      link = `/organization/${organizationId}/users/${userId}`;
    }

    return (
      <tr
        className={classNames(
          this.isMembership() ? "membership" : "invite",
          "table-row",
          this.props.userRelation.fresh && "new",
        )}
        data-id={this.props.userRelation.email}
      >
        {this.props.renderName && (
          <td>
            {link ? (
              <a className="user-detail-link" href={link}>
                {this.getName()}
              </a>
            ) : (
              this.getName()
            )}
          </td>
        )}
        <td>{this.props.userRelation.email}</td>
        <td>{this.props.userRelation.owner ? "Owner" : "Member"}</td>
        <td>{renderTeams()}</td>
        <td>
          {renderEditButton()}
          {renderUninviteButton()}
        </td>
      </tr>
    );
  }
}
