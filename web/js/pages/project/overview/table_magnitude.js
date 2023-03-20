/**
 * Copyright © 2022 Intel Corporation
 *
 * SPDX-License-Identifier: Apache License 2.0
 */

import _ from "underscore";
import React from "react";
import classNames from "classnames";

import AngleDownGlyph from "../../../component/glyph/angle-down";
import Component from "../../../react/component";
import Loading from "../../../component/loading";
import ui from "../../../experiment/ui";
import {Dropdown, DropdownItem} from "../../../component/dropdown";
import {MILLISECONDS_PER_SECOND} from "../../../constants";
import {
  eachWithDelay,
  isDefinedAndNotNull,
  isUndefinedOrNull,
  renderNumber,
  uniformRandomNumberGenerator,
} from "../../../utils";
import {unarchivedRunsFilter} from "../../../training_run/constants";

const maxRows = 10;
const maxRowsForExperimentRuns = 3;

const Table = ({children}) => <table className="table">{children}</table>;

const Cell = ({children, className}) => (
  <td className={className}>
    <div className="cell-content">{children}</div>
  </td>
);

const BasicResourceRow = ({
  collapsable,
  collapsed,
  focused,
  onHover,
  onToggle,
  resource,
  runCount,
}) => {
  const typeDisplay =
    {
      experiment: "Experiment",
      run: "Run",
    }[resource.type] || null;
  const widthPercent = resource.displayValue * 100;
  const rowCollapsedClass = collapsed ? "collapsed" : "";
  return (
    <tr
      className={classNames(
        "resource-row",
        resource.type,
        {focused},
        rowCollapsedClass,
      )}
      onMouseEnter={onHover}
    >
      <Cell className="bar-cell">
        <div className="bar-magnitude" style={{width: `${widthPercent}%`}} />
      </Cell>
      <Cell className="metric-cell">
        <span title={resource.value}>{renderNumber(resource.value, 12)}</span>
      </Cell>
      <Cell className="type-cell">
        <span>
          {resource.type === "experiment" && runCount
            ? `${typeDisplay} (${runCount} runs)`
            : typeDisplay}
        </span>
      </Cell>
      <Cell className="name-cell">
        <a href={resource.url}>{resource.name}</a>
      </Cell>
      <Cell className="caret-cell">
        {collapsable ? (
          <button
            className="toggler"
            type="button"
            data-toggle="collapse"
            data-target={`#${resource.key}`}
            aria-controls={resource.key}
            aria-expanded="false"
            aria-label="Toggle navigation"
            onClick={onToggle}
          >
            <AngleDownGlyph />
          </button>
        ) : null}
      </Cell>
    </tr>
  );
};

class InnerRunRow extends React.Component {
  onHover = () => {
    if (this.props.onResourceFocus) {
      this.props.onResourceFocus(this.props.resource.origin);
    }
  };

  render() {
    return <BasicResourceRow {...this.props} onHover={this.onHover} />;
  }
}

class ExperimentRow extends Component {
  state = {
    collapsed: true,
    runCount: null,
  };

  componentDidMount() {
    this.services.promiseApiClient
      .clients(this.props.project.client)
      .projects(this.props.project.id)
      .trainingRuns()
      .fetch({
        filters: JSON.stringify([
          {
            field: "experiment",
            operator: "==",
            value: this.props.resource.origin.id,
          },
        ]),
        limit: 0,
      })
      .then(({count}) => this.setState({runCount: count}));
  }

  onHover = () => {
    if (this.props.onResourceFocus) {
      this.props.onResourceFocus(this.props.resource.origin);
    }
  };

  onToggle = () => {
    this.setState((state) => ({collapsed: !state.collapsed}));
  };

  render() {
    const {focusedResource, project, onResourceFocus, resource} = this.props;
    const {collapsed, runCount} = this.state;
    const thisFocused = focusedResource === resource.origin;
    return (
      <div>
        <Table>
          <tbody>
            <BasicResourceRow
              collapsable={true}
              collapsed={collapsed}
              onToggle={this.onToggle}
              focused={thisFocused}
              onHover={this.onHover}
              resource={resource}
              runCount={runCount}
            />
          </tbody>
        </Table>
        <div className="collapse" id={resource.key}>
          <Table>
            <tbody>
              {_.map(resource.runResources, (subResource) => (
                <InnerRunRow
                  key={subResource.url}
                  focused={
                    thisFocused || focusedResource === subResource.origin
                  }
                  onResourceFocus={onResourceFocus}
                  resource={subResource}
                />
              ))}
              <tr
                className={focusedResource === resource.origin ? "focused" : ""}
              >
                <td className="view-all" colSpan={5}>
                  <Loading loading={isUndefinedOrNull(runCount)}>
                    <a
                      href={`/client/${project.client}/project/${project.id}/runs`}
                    >
                      View all {runCount} runs in {resource.name}
                    </a>
                  </Loading>
                </td>
              </tr>
            </tbody>
          </Table>
        </div>
      </div>
    );
  }
}

const RunRow = (props) => (
  <Table>
    <tbody>
      <InnerRunRow
        {...props}
        focused={props.focusedResource === props.resource.origin}
      />
    </tbody>
  </Table>
);

const TableMagRow = ({focusedResource, onResourceFocus, project, resource}) => {
  const RowComponent = {
    experiment: ExperimentRow,
    run: RunRow,
  }[resource.type];
  return RowComponent ? (
    <div className={classNames("row-wrapper", resource.type)}>
      <RowComponent
        focusedResource={focusedResource}
        onResourceFocus={onResourceFocus}
        project={project}
        resource={resource}
      />
    </div>
  ) : null;
};

class ToggleAscending extends React.Component {
  setHighest = () => this.props.onChange(false);
  setLowest = () => this.props.onChange(true);

  render() {
    const {ascending} = this.props;
    return (
      <div className="order">
        <button
          className={classNames("btn btn-sm left-joined-button", {
            active: !ascending,
          })}
          onClick={this.setHighest}
          type="button"
          value="Highest"
        >
          Highest
        </button>
        <button
          className={classNames("btn btn-sm right-joined-button", {
            active: ascending,
          })}
          onClick={this.setLowest}
          type="button"
          value="Lowest"
        >
          Lowest
        </button>
      </div>
    );
  }
}

class SelectMetric extends React.Component {
  render() {
    const {onChange, metric, options} = this.props;
    return (
      <Dropdown buttonClassName="btn btn-sm" label={metric}>
        {_.map(options, (metricOption) => (
          <DropdownItem key={metricOption}>
            <a onClick={() => onChange(metricOption)}>{metricOption}</a>
          </DropdownItem>
        ))}
      </Dropdown>
    );
  }
}

const getMetricKey = (experiment, metricInfo) =>
  `${experiment.id}:${metricInfo.key}`;

const getGlobalRunKey = (key) => `global:${key}`;

const getExperimentRunKey = (experiment, key) =>
  `experiment:${experiment.id}:${key}`;

const runToResource = (run, selectedMetricInfo) => {
  const value = (run.values[selectedMetricInfo.metric] || {}).value;
  return {
    name: run.name,
    origin: run,
    type: "run",
    updated: run.updated,
    url: `/run/${run.id}`,
    value: isDefinedAndNotNull(value) ? value : null,
  };
};

class TableMagnitudeContent extends Component {
  constructor(props) {
    super(props);
    const metric = _.first(this.props.metrics);
    this.state = {
      experimentCache: _.indexBy(this.props.experiments, "id"),
      metricCache: {},
      runCache: {},
      selectedMetricInfo: {
        ascending: false,
        key: `${metric}:${false}`,
        metric,
      },
    };
  }

  componentDidMount() {
    this.updateView();
  }

  componentDidUpdate(prevProps, prevState) {
    if (
      !_.isEqual(this.state.selectedMetricInfo, prevState.selectedMetricInfo)
    ) {
      this.updateView();
    }
  }

  updateView = () => {
    this.updateBestExperiments();
    this.updateBestRuns();
  };

  updateBestExperiments = () => {
    const {selectedMetricInfo} = this.state;
    const updateMetricCache = (state, metricKey, newCache) => ({
      metricCache: _.extend({}, state.metricCache, {[metricKey]: newCache}),
    });
    const fetchExperimentData = (experiment) => {
      this.setState((state) => {
        const metricKey = getMetricKey(experiment, selectedMetricInfo);
        if (state.metricCache[metricKey]) {
          return {};
        }
        return updateMetricCache(state, metricKey, {
          promise: this.services.promiseApiClient
            .clients(this.props.project.client)
            .projects(this.props.project.id)
            .trainingRuns()
            .fetch({
              ascending: selectedMetricInfo.ascending,
              limit: 1,
              sort: `values.${selectedMetricInfo.metric}.value`,
              filters: JSON.stringify([
                {
                  field: "experiment",
                  operator: "==",
                  value: experiment.id,
                },
                unarchivedRunsFilter,
              ]),
            })
            .then(({data}) =>
              this.setState((s) => {
                const metricValue = _.chain(data)
                  .pluck("values")
                  .pluck(selectedMetricInfo.metric)
                  .pluck("value")
                  .first()
                  .value();
                return updateMetricCache(s, metricKey, {
                  value: isDefinedAndNotNull(metricValue) ? metricValue : null,
                });
              }),
            ),
        });
      });
      const {ascending, metric, key} = selectedMetricInfo;
      const query = {
        sort: `values.${metric}.value`,
        ascending,
        limit: maxRowsForExperimentRuns,
        filters: JSON.stringify([
          {
            field: "experiment",
            operator: "==",
            value: experiment.id,
          },
          unarchivedRunsFilter,
        ]),
      };
      this.fetchRuns(getExperimentRunKey(experiment, key), query);
    };
    eachWithDelay(
      this.state.experimentCache,
      fetchExperimentData,
      uniformRandomNumberGenerator(
        50 / MILLISECONDS_PER_SECOND,
        150 / MILLISECONDS_PER_SECOND,
      ),
    );
  };

  updateBestRuns = () => {
    const {ascending, metric, key} = this.state.selectedMetricInfo;
    const query = {
      sort: `values.${metric}.value`,
      ascending,
      limit: maxRows,
      filters: JSON.stringify([
        {
          field: "experiment",
          operator: "isnull",
        },
        unarchivedRunsFilter,
      ]),
    };
    this.fetchRuns(getGlobalRunKey(key), query);
  };

  fetchRuns = (key, query) => {
    const updateState = (state, newCache) => ({
      runCache: _.extend({}, state.runCache, {[key]: newCache}),
    });
    this.setState((state) => {
      if (state.runCache[key]) {
        return {};
      }
      return updateState(state, {
        promise: this.services.promiseApiClient
          .clients(this.props.project.client)
          .projects(this.props.project.id)
          .trainingRuns()
          .fetch(query)
          .then(({data}) => this.setState((s) => updateState(s, {runs: data}))),
      });
    });
  };

  updateSelectedMetric = (selectedMetricInfo) =>
    this.setState({selectedMetricInfo});

  getResourcesForTable = () => {
    const {selectedMetricInfo} = this.state;
    const experimentResources = _.chain(this.state.experimentCache)
      .values()
      .map((experiment) => {
        const metricKey = getMetricKey(experiment, selectedMetricInfo);
        const cachedMetric = this.state.metricCache[metricKey];
        if (!cachedMetric || cachedMetric.promise) {
          return null;
        }
        const cachedRuns =
          this.state.runCache[
            getExperimentRunKey(experiment, selectedMetricInfo.key)
          ];
        if (!cachedRuns || cachedRuns.promise) {
          return null;
        }
        return {
          key: `experiment${experiment.id}`,
          name: experiment.name,
          origin: experiment,
          runResources: _.map(cachedRuns.runs, (run) =>
            runToResource(run, selectedMetricInfo),
          ),
          type: "experiment",
          updated: experiment.updated,
          url: ui.getExperimentUrl(experiment),
          value: isDefinedAndNotNull(cachedMetric.value)
            ? cachedMetric.value
            : null,
        };
      })
      .value();
    // this indicates that we don't yet know what the values for all the experiments are
    if (!_.all(experimentResources)) {
      return null;
    }
    const runCache =
      this.state.runCache[getGlobalRunKey(selectedMetricInfo.key)];
    if (!runCache || !runCache.runs) {
      return null;
    }
    const runResources = _.chain(runCache.runs)
      .map((run) => runToResource(run, selectedMetricInfo))
      .value();
    const topResources = _.chain([experimentResources, runResources])
      .flatten()
      .filter(({value}) => isDefinedAndNotNull(value))
      .sortBy(({value}) => value * (selectedMetricInfo.ascending ? 1 : -1))
      .first(maxRows)
      .value();
    const allResources = _.flatten([
      [topResources],
      _.map(topResources, (r) => r.runResources || []),
    ]);
    const metricWindow = {
      min: 0,
      max: 1,
    };
    if (_.size(allResources) > 0) {
      const valuesChain = _.chain(allResources).pluck("value");
      const [minValue, maxValue] = [
        valuesChain.min().value(),
        valuesChain.max().value(),
      ];
      const valueDelta = maxValue - minValue;
      const offset = valueDelta > 0 ? valueDelta * 0.5 : 1;
      const {ascending} = selectedMetricInfo;
      metricWindow.min = minValue - (ascending ? 0 : offset);
      metricWindow.max = maxValue + (ascending ? offset : 0);
      const outerPadding = 0.1 * (metricWindow.max - metricWindow.min);
      metricWindow.min -= outerPadding;
      metricWindow.max += outerPadding;
    }
    _.each(allResources, (resource) => {
      resource.displayValue =
        (resource.value - metricWindow.min) /
        (metricWindow.max - metricWindow.min);
    });
    return topResources;
  };

  setAscending = (ascending) =>
    this.setState(({selectedMetricInfo}) => {
      if (selectedMetricInfo.ascending === ascending) {
        return {};
      }
      return {
        selectedMetricInfo: _.extend({}, selectedMetricInfo, {
          ascending,
          key: `${selectedMetricInfo.metric}:${ascending}`,
        }),
      };
    });

  setMetric = (metric) =>
    this.setState(({selectedMetricInfo}) => {
      if (selectedMetricInfo.metric === metric) {
        return {};
      }
      return {
        selectedMetricInfo: _.extend({}, selectedMetricInfo, {
          key: `${metric}:${selectedMetricInfo.ascending}`,
          metric,
        }),
      };
    });

  render() {
    const {selectedMetricInfo} = this.state;
    const resources = this.getResourcesForTable();
    return (
      <div className="table-magnitude">
        <div className="header-group">
          <Table>
            <thead>
              <tr>
                <th className="bar-cell">
                  <ToggleAscending
                    onChange={this.setAscending}
                    ascending={Boolean(selectedMetricInfo.ascending)}
                  />
                </th>
                <th className="metric-cell">
                  <SelectMetric
                    onChange={this.setMetric}
                    metric={selectedMetricInfo.metric}
                    options={this.props.metrics}
                  />
                </th>
                <th className="type-cell">Type</th>
                <th className="name-cell">Name</th>
                <th className="caret-cell" />
              </tr>
            </thead>
          </Table>
        </div>
        <div className="body-group">
          <Loading loading={!resources}>
            {_.map(resources, (resource) => (
              <TableMagRow
                key={resource.url}
                focusedResource={this.props.focusedResource}
                onResourceFocus={this.props.onResourceFocus}
                project={this.props.project}
                resource={resource}
              />
            ))}
          </Loading>
        </div>
      </div>
    );
  }
}

export default class TableMagnitude extends React.Component {
  render() {
    if (_.isEmpty(this.props.metrics)) {
      return (
        <span>
          No metrics have been reported yet. Log metrics for your runs so that
          you can view the best ones here.
        </span>
      );
    }
    return <TableMagnitudeContent {...this.props} />;
  }
}
