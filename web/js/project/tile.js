/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";
import pluralize from "pluralize";

import AsynchronousUserName from "../user/name_span";
import schemas from "../react/schemas";
import {RelativeTime} from "../render/format_times";
import {isDefinedAndNotNull} from "../utils";

export default class ProjectTile extends React.Component {
  static propTypes = {
    includeClient: PropTypes.bool.isRequired,
    project: schemas.Project.isRequired,
    userDataSources: PropTypes.object,
  };

  render() {
    const pluralizedExpLabel = pluralize(
      "experiment",
      this.props.project.experiment_count,
    );
    const pluralizedRunLabel = pluralize(
      "run",
      this.props.project.training_run_count,
    );
    return (
      <a
        className="tile project"
        href={`/client/${this.props.project.client}/project/${this.props.project.id}`}
        title={this.props.project.name}
      >
        <div
          className={classNames("project-title", {
            archived: this.props.project.deleted,
          })}
        >
          {this.props.project.deleted && (
            <span className="archived-text">Archived</span>
          )}
          <h4 className="truncated">{this.props.project.name}</h4>
          <p>{`${this.props.project.experiment_count} ${pluralizedExpLabel}`}</p>
          <p>
            {`${
              isDefinedAndNotNull(this.props.project.training_run_count)
                ? this.props.project.training_run_count
                : "-"
            } ${pluralizedRunLabel}`}
          </p>
        </div>
        <div className="project-metadata">
          <span>Updated </span>
          <RelativeTime time={this.props.project.updated} />
          {this.props.includeClient && this.props.project.user && (
            <div>
              <span>Created by: </span>
              <AsynchronousUserName
                className="truncated"
                dataSource={this.props.userDataSources.get(
                  this.props.project.user,
                )}
              />
            </div>
          )}
        </div>
      </a>
    );
  }
}
