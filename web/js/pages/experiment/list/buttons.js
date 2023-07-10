/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

/* eslint-disable react/jsx-no-bind */
import "../../../../styles/less/experiment/list_buttons.less";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";
import pluralize from "pluralize";

import Loading from "../../../component/loading";

export const ViewToggle = function (props) {
  const userTitle = "Mine";
  const clientTitle = "Team";
  return (
    <div className="view-button-wrapper">
      <Button
        active={!props.includeClient}
        buttonTitle={userTitle}
        classNames={["left-joined-button"]}
        onClick={props.includeClient ? props.onToggle : _.noop}
      />
      <Button
        active={props.includeClient}
        buttonTitle={clientTitle}
        classNames={["right-joined-button"]}
        onClick={props.includeClient ? _.noop : props.onToggle}
      />
    </div>
  );
};

ViewToggle.propTypes = {
  includeClient: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
};

export const FilterCheckbox = function (props) {
  return (
    <div className="filter-toggle-wrapper">
      <div className="filter-toggle-label">{props.label}</div>
      <div className="filter-toggle-holder">
        <div className="filter-toggle" onClick={props.onClick}>
          <input type="checkbox" id={props.id} defaultChecked={props.checked} />
          <label />
        </div>
      </div>
    </div>
  );
};

FilterCheckbox.propTypes = {
  checked: PropTypes.bool.isRequired,
  id: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
};

const Button = function (props) {
  const buttonClassNames = classNames(
    "btn",
    props.active ? "active-button" : "inactive-button",
    props.classNames,
  );
  return (
    <button className={buttonClassNames} onClick={props.onClick} type="button">
      {props.buttonTitle}
    </button>
  );
};

Button.propTypes = {
  active: PropTypes.bool.isRequired,
  buttonTitle: PropTypes.string.isRequired,
  classNames: PropTypes.arrayOf(PropTypes.string),
  onClick: PropTypes.func.isRequired,
};

export const FilterButtonHolder = function (props) {
  const view = {
    includeClient: props.includeClient,
    archived: props.archived,
    dev: props.dev,
  };
  const onClick = (d) => {
    props.pushViewHistory(_.extend(view, d));
    props.clearSelectedExperiments();
  };
  return (
    <div className="view-button-holder">
      {props.showClientExperiments && !props.isProjectPage ? (
        <ViewToggle
          includeClient={props.includeClient}
          onToggle={() => onClick({includeClient: !props.includeClient})}
        />
      ) : null}
      <FilterCheckbox
        checked={props.archived}
        label="Show Archived"
        id="archive-toggle"
        onClick={() => onClick({archived: !props.archived})}
      />
      {props.isAiExperiment ? null : (
        <FilterCheckbox
          checked={props.dev}
          label="Show Development"
          id="dev-toggle"
          onClick={() => onClick({dev: !props.dev})}
        />
      )}
    </div>
  );
};

FilterButtonHolder.propTypes = {
  archived: PropTypes.bool.isRequired,
  clearSelectedExperiments: PropTypes.func.isRequired,
  dev: PropTypes.bool.isRequired,
  includeClient: PropTypes.bool.isRequired,
  isAiExperiment: PropTypes.bool.isRequired,
  isProjectPage: PropTypes.bool.isRequired,
  pushViewHistory: PropTypes.func.isRequired,
  showClientExperiments: PropTypes.bool,
};

export class BulkActionButtonHolder extends React.Component {
  static propTypes = {
    archiveSelectedExperiments: PropTypes.func.isRequired,
    loading: PropTypes.bool.isRequired,
    numSelected: PropTypes.number.isRequired,
    unarchiveSelectedExperiments: PropTypes.func.isRequired,
  };

  render() {
    const buttonOrPlaceholder =
      this.props.numSelected > 0 ? (
        <div className="form-group bulk-button-row">
          <Loading loading={this.props.loading}>
            <div className="bulk-action-label">
              {`${pluralize(
                "experiment",
                this.props.numSelected,
                true,
              )} selected`}
            </div>
            <div className="input-group">
              <Button
                active={false}
                buttonTitle="Archive"
                onClick={this.props.archiveSelectedExperiments}
              />
              <Button
                active={false}
                buttonTitle="Unarchive"
                onClick={this.props.unarchiveSelectedExperiments}
              />
            </div>
          </Loading>
        </div>
      ) : (
        <div className="form-group bulk-button-row" />
      );
    return (
      <div className="bulk-button-wrapper">
        <div className="bulk-button-holder">{buttonOrPlaceholder}</div>
      </div>
    );
  }
}
