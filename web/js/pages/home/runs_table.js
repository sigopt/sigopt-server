/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import "../../render/bootstrap";

import _ from "underscore";
import PropTypes from "prop-types";
import React from "react";
import classNames from "classnames";

import AngleDownGlyph from "../../component/glyph/angle-down";
import Component from "../../react/component";
import CustomTooltip from "../../component/custom_tooltip";
import {Duration, RelativeTime} from "../../render/format_times";
import {isNotNothing} from "../../utils";
import {statusGlyphs} from "../training_run/constants";

class RunRow extends Component {
  static defaultProps = {
    enableCollapse: true,
  };

  state = {
    collapsed: true,
  };

  render() {
    // The header label should only be applied to the first row of the table
    const parametersHeader = ["Parameters:"];
    const parameters = _.chain(this.props.run.assignments)
      .pairs()
      .map((p, idx) => ({
        label: parametersHeader[idx],
        parameter: p[0],
        value: p[1],
      }))
      .value();
    const metricsHeader = ["Metrics:"];
    const metrics = _.chain(this.props.run.values)
      .values()
      .map((val, idx) => ({
        label: metricsHeader[idx],
        metric: val.name,
        value: val.value,
      }))
      .value();
    return (
      <>
        <tr className="run">
          {_.map(this.props.columns, ({Cell}, i) => (
            <Cell key={i} run={this.props.run} />
          ))}
          {this.props.enableCollapse ? (
            <td>
              <button
                className="btn collapsed"
                type="button"
                data-toggle="collapse"
                data-target={`#run-${this.props.run.id}-details`}
                aria-controls={`#run-${this.props.run.id}-details`}
                aria-expanded="false"
                aria-label="Toggle run details"
              >
                <AngleDownGlyph
                  className={this.state.collapsed ? "collapsed" : ""}
                />
              </button>
            </td>
          ) : null}
        </tr>
        {this.props.enableCollapse ? (
          <tr
            className="collapse run-details"
            key={`run-${this.props.run.id}-details`}
            id={`run-${this.props.run.id}-details`}
          >
            <td />
            <td colSpan={this.props.headerCount}>
              <table>
                <tbody>
                  {_.map(metrics, (m) => (
                    <tr key={`run-${this.props.run.id}-metrics-${m.metric}`}>
                      <th>{m.label}</th>
                      <td>{m.metric}</td>
                      <td>{m.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <table>
                <tbody>
                  {_.map(parameters, (p) => (
                    <tr
                      key={`run-${this.props.run.id}-parameters-${p.parameter}`}
                    >
                      <th>{p.label}</th>
                      <td>{p.parameter}</td>
                      <td>{p.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <table key={`run-${this.props.run.id}-info`}>
                <tbody>
                  <tr key={`run-${this.props.run.id}-id`}>
                    <th>Run ID:</th>
                    <td>{this.props.run.id}</td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        ) : null}
      </>
    );
  }
}

export const runStatusColumn = {
  Header: () => <th>Status</th>,
  Cell: (props) => {
    const Glyph = statusGlyphs[props.run.state];
    return (
      <td>
        <CustomTooltip html={true} tooltip={<span>{props.run.state}</span>}>
          <Glyph className={classNames("tooltip-trigger", props.run.state)} />
        </CustomTooltip>
      </td>
    );
  },
};

export const runIdColumn = {
  Header: () => <th>Run ID</th>,
  Cell: (props) => (
    <td>
      <a href={`/run/${props.run.id}`}>{props.run.id}</a>
    </td>
  ),
};

export const runNameColumn = {
  Header: () => <th>Run Name</th>,
  Cell: (props) => (
    <td>
      <a href={`/run/${props.run.id}`}>{props.run.name}</a>
    </td>
  ),
};

export const runDurationColumn = {
  Header: () => <th>Duration</th>,
  Cell: (props) => (
    <td>
      <Duration
        endTime={props.run.completed || Date.now() / 1000}
        startTime={props.run.created}
      />
    </td>
  ),
};

export const runUpdatedColumn = {
  Header: () => <th>Last Updated</th>,
  Cell: (props) => (
    <td>
      <RelativeTime time={props.run.updated} />
    </td>
  ),
};

export const runCreatedColumn = {
  Header: () => <th>Created</th>,
  Cell: (props) => (
    <td>
      <RelativeTime time={props.run.created} />
    </td>
  ),
};

export const runCheckpointsColumn = {
  Header: () => <th>Checkpoints</th>,
  Cell: (props) => <td>{props.run.checkpoint_count}</td>,
};

export const runModelTypeColumn = {
  Header: () => <th>Model Type</th>,
  Cell: (props) => <td>{props.run.model.type}</td>,
};

export const runExperimentColumn = {
  Header: () => <th>Experiment</th>,
  Cell: (props) => (
    <td>
      {props.run.experiment ? (
        <a href={`/aiexperiment/${props.run.experiment}`}>
          {props.run.experiment}
        </a>
      ) : null}
    </td>
  ),
};

export const runProjectColumn = {
  Header: () => <th>Project</th>,
  Cell: (props) => (
    <td>
      <a href={`/client/${props.run.client}/project/${props.run.project}`}>
        {props.run.project}
      </a>
    </td>
  ),
};

export const basicRunColumns = [
  runStatusColumn,
  runIdColumn,
  runNameColumn,
  runUpdatedColumn,
  runCreatedColumn,
  runCheckpointsColumn,
  runModelTypeColumn,
];

export default class RunsTable extends Component {
  static propTypes = {
    columns: PropTypes.arrayOf(PropTypes.object),
    enableCollapse: PropTypes.bool,
    nullContent: PropTypes.node,
    promiseApiClient: PropTypes.object.isRequired,
    runs: PropTypes.arrayOf(PropTypes.object),
  };

  static defaultProps = {
    columns: [...basicRunColumns, runExperimentColumn, runProjectColumn],
  };

  render() {
    const hasData = isNotNothing(this.props.runs);
    const countableHeaders = _.map(this.props.columns, ({Header}, i) => (
      <Header key={i} />
    ));

    return (
      <div className="table-container runs-table">
        <table className="table table-responsive">
          <thead>
            <tr>
              {countableHeaders}
              <th className="accordion-button-col" />
            </tr>
          </thead>
          <tbody>
            {hasData ? (
              _.map(this.props.runs, (run) => (
                <RunRow
                  key={`run-${run.id}-row`}
                  enableCollapse={this.props.enableCollapse}
                  headerCount={_.size(countableHeaders)}
                  columns={this.props.columns}
                  promiseApiClient={this.props.promiseApiClient}
                  run={run}
                />
              ))
            ) : (
              <tr>
                <td colSpan={10}>
                  {this.props.nullContent ? (
                    this.props.nullContent
                  ) : (
                    <p>0 runs</p>
                  )}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  }
}
