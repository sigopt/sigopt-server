/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import $ from "jquery";
import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";
import pluralize from "pluralize";

import AsynchronousUserName from "../../../user/name_span";
import Component from "../../../react/component";
import EllipsisVerticalGlyph from "../../../component/glyph/ellipsis-vertical";
import Loading from "../../../component/loading";
import ShareExperimentModal from "../../../share/share_modal_one";
import schemas from "../../../react/schemas";
import ui from "../../../experiment/ui";
import {CompactExperimentProgress} from "../../../experiment/progress";
import {Dropdown, DropdownItem} from "../../../component/dropdown";
import {EXPERIMENT_STATE_ENUM} from "./constants";
import {RelativeTime} from "../../../render/format_times";
import {
  renderNumber,
  withPreventDefault,
  withStopPropagation,
} from "../../../utils";

const ClickableCell = function (props) {
  return (
    <td className={classNames(props.classNames)}>
      <a className="clickable" href={ui.getExperimentUrl(props.experiment)}>
        {props.children}
      </a>
    </td>
  );
};

ClickableCell.propTypes = {
  children: PropTypes.oneOfType([PropTypes.any]),
  classNames: PropTypes.arrayOf(PropTypes.string),
  experiment: schemas.Experiment.isRequired,
};

class SelectBoxCell extends Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    reload: PropTypes.func.isRequired,
    selected: PropTypes.bool.isRequired,
    toggleExperimentSelection: PropTypes.func.isRequired,
  };

  render() {
    const id = `checkbox-experiments-${this.props.experiment.id}`;
    return (
      <td>
        <div className="checkbox">
          <input
            type="checkbox"
            id={id}
            checked={this.props.selected}
            onChange={(e) => {
              this.props.toggleExperimentSelection(
                this.props.experiment.id,
                e.target.checked,
                this.props.reload,
              );
            }}
          />
          <label htmlFor={id} />
        </div>
      </td>
    );
  }
}

class ExperimentNameCell extends Component {
  static propTypes = {
    experimentName: PropTypes.string.isRequired,
  };

  render() {
    return (
      <ClickableCell {...this.props}>
        <p
          className="experiment-name truncated"
          title={this.props.experimentName}
        >
          {this.props.experimentName}
        </p>
      </ClickableCell>
    );
  }
}

class ProgressCell extends Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
  };

  render() {
    const progress = (
      <CompactExperimentProgress experiment={this.props.experiment} />
    );
    return (
      <ClickableCell {...this.props}>
        <div className="progress-width">{progress}</div>
      </ClickableCell>
    );
  }
}

export class MetricCell extends Component {
  static propTypes = {
    bestAssignments: PropTypes.arrayOf(schemas.BestAssignment),
    experiment: schemas.Experiment.isRequired,
  };

  render() {
    const mostImportantMetricName =
      ui.mostImportantMetrics(this.props.experiment)[0].name || null;
    const bestObservation =
      (this.props.bestAssignments && _.first(this.props.bestAssignments)) ||
      null;
    // NOTE: safety-check if only failed observations
    const bestValue =
      (bestObservation?.values?.[0] &&
        ui.optimizedValues(this.props.experiment, bestObservation.values)[0]) ??
      "N/A";
    return (
      <>
        <p className="best-value metric-value">
          {renderNumber(bestValue, true)}
        </p>{" "}
        {mostImportantMetricName && (
          <p
            className="best-value-label truncated"
            title={mostImportantMetricName}
          >
            {mostImportantMetricName}
          </p>
        )}
      </>
    );
  }
}

export class NumSolutionsCell extends Component {
  static propTypes = {
    bestAssignments: PropTypes.arrayOf(schemas.BestAssignment),
  };

  render() {
    const numBestAssignments = _.size(this.props.bestAssignments);
    const valueStr = pluralize("Value", numBestAssignments);
    return (
      <>
        <p className="best-value num-solutions-value">{numBestAssignments}</p>{" "}
        <p className="best-value-label truncated">{`Best ${valueStr} found`}</p>
      </>
    );
  }
}

class BestValueCell extends Component {
  static propTypes = {
    experiment: schemas.Experiment.isRequired,
    promiseApiClient: PropTypes.object.isRequired,
  };

  state = {
    bestAssignments: null,
    loadingBestAssignments: true,
  };

  componentDidMount() {
    this._isMounted = true;
    this.props.promiseApiClient
      .experiments(this.props.experiment.id)
      .bestAssignments()
      .exhaustivelyPage()
      .then((bestAssignments) => {
        if (this._isMounted) {
          this.setState({
            bestAssignments: bestAssignments,
            loadingBestAssignments: false,
          });
        }
      });
  }

  componentWillUnmount() {
    this._isMounted = false;
  }

  render() {
    return (
      <ClickableCell {...this.props}>
        <div className="best-value-wrapper">
          <Loading loading={this.state.loadingBestAssignments}>
            {ui.isParetoOptimizedExperiment(this.props.experiment) ||
            ui.isSearchExperiment(this.props.experiment) ? (
              <NumSolutionsCell bestAssignments={this.state.bestAssignments} />
            ) : (
              <MetricCell
                bestAssignments={this.state.bestAssignments}
                experiment={this.props.experiment}
              />
            )}
          </Loading>
        </div>
      </ClickableCell>
    );
  }
}

const ArchiveLabelCell = function (props) {
  return (
    <ClickableCell {...props}>
      {props.experiment.state === EXPERIMENT_STATE_ENUM.deleted && (
        <div className="pill-holder archived-pill">
          <div className="pill-label">Archived</div>
        </div>
      )}
    </ClickableCell>
  );
};

const DevLabelCell = function (props) {
  return (
    <ClickableCell {...props}>
      {props.experiment.development && (
        <div className="pill-holder dev-pill">
          <div className="pill-label">Dev</div>
        </div>
      )}
    </ClickableCell>
  );
};

const LastUpdatedCell = function (props) {
  return (
    <ClickableCell {...props}>
      <div className="timestamp">
        {<RelativeTime time={props.experiment.updated} />}
      </div>
    </ClickableCell>
  );
};

const ProjectCell = function (props) {
  return (
    <ClickableCell {...props}>
      <div>
        <p className="project-name truncated">{props.project}</p>
      </div>
    </ClickableCell>
  );
};

const UserNameCell = function (props) {
  return (
    <ClickableCell {...props}>
      {props.showCreatedBy && props.experiment.user && (
        <div className="user-name-span truncated">
          <AsynchronousUserName
            dataSource={props.userDataSources.get(props.experiment.user)}
          />
        </div>
      )}
    </ClickableCell>
  );
};

class ActionCell extends Component {
  constructor(...args) {
    super(...args);
    this._node = React.createRef();
  }

  onClick = () => {
    const $td = $(this._node.current);
    const $dropdown = $td.find(".dropdown-toggle");
    $dropdown.dropdown("toggle");
  };

  archiveClick = () => {
    this.services.promiseApiClient
      .experiments(this.props.experiment.id)
      .delete()
      .then(this.props.reload);
  };

  unarchiveClick = () => {
    this.services.promiseApiClient
      .experiments(this.props.experiment.id)
      .update({state: "active"})
      .then(this.props.reload);
  };

  render() {
    return (
      <td className="action-cell" ref={this._node}>
        {(this.props.canEdit || this.props.canShare) && (
          <Dropdown
            buttonClassName="action-button"
            caret={false}
            direction="up"
            label={<EllipsisVerticalGlyph />}
            onClick={withStopPropagation(_.identity)}
            ref={(c) => {
              this._dropdown = c;
            }}
          >
            {this.props.canEdit && (
              <DropdownItem>
                {this.props.experiment.state ===
                EXPERIMENT_STATE_ENUM.deleted ? (
                  <span
                    className="archive"
                    onClick={withPreventDefault(this.unarchiveClick)}
                  >
                    Unarchive
                  </span>
                ) : (
                  <span
                    className="archive"
                    onClick={withPreventDefault(this.archiveClick)}
                  >
                    Archive
                  </span>
                )}
              </DropdownItem>
            )}
            {this.props.canShare && (
              <DropdownItem>
                <span
                  className="share"
                  onClick={withPreventDefault(this.props.shareClick)}
                >
                  Share
                </span>
              </DropdownItem>
            )}
          </Dropdown>
        )}
      </td>
    );
  }
}

export default class ExperimentRow extends Component {
  static propTypes = {
    canEdit: PropTypes.bool.isRequired,
    canShare: PropTypes.bool.isRequired,
    experiment: schemas.Experiment.isRequired,
    includeProject: PropTypes.bool.isRequired,
    isAiExperiment: PropTypes.bool.isRequired,
    reload: PropTypes.func.isRequired,
    selected: PropTypes.bool.isRequired,
    showCreatedBy: PropTypes.bool.isRequired,
    toggleExperimentSelection: PropTypes.func.isRequired,
    userDataSources: PropTypes.object.isRequired,
  };

  shareClick = () => {
    this._shareModal.show();
  };

  render() {
    const e = this.props.experiment;
    const clickableProps = {
      experiment: e,
      navigator: this.services.navigator,
    };
    return (
      <>
        <tr
          className={classNames("experiment-row", {
            aiexperiment: ui.isAiExperiment(e),
          })}
          key={e.id}
        >
          <SelectBoxCell
            experiment={e}
            reload={this.props.reload}
            toggleExperimentSelection={this.props.toggleExperimentSelection}
            selected={this.props.selected}
          />
          <ClickableCell {...clickableProps}>
            <div className="id-cell">
              <p className="id-cell">{e.id}</p>
            </div>
          </ClickableCell>
          <ExperimentNameCell experimentName={e.name} {...clickableProps} />
          <ProgressCell experiment={e} {...clickableProps} />
          <BestValueCell
            experiment={e}
            index={0}
            promiseApiClient={this.services.promiseApiClient}
            {...clickableProps}
          />
          <ArchiveLabelCell {...clickableProps} />
          <DevLabelCell {...clickableProps} />
          <LastUpdatedCell {...clickableProps} />
          {this.props.includeProject && this.props.isAiExperiment ? (
            <ProjectCell
              showProject={this.props.includeProject}
              project={e.project}
              {...clickableProps}
            />
          ) : null}
          {this.props.showCreatedBy ? (
            <UserNameCell
              showCreatedBy={this.props.showCreatedBy}
              userDataSources={this.props.userDataSources}
              {...clickableProps}
            />
          ) : null}
          <ActionCell
            shareClick={this.shareClick}
            promiseApiClient={this.services.promiseApiClient}
            {...this.props}
          />
        </tr>
        {this.props.canShare && (
          <ShareExperimentModal
            alertBroker={this.services.alertBroker}
            experiment={e}
            ref={(c) => (this._shareModal = c)}
          />
        )}
      </>
    );
  }
}
